from functools import wraps

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from accounts.decorators import role_required
from notifications.utils import notify

from .models import BLOOD_GROUPS, BloodInventory, BloodRequest

GROUPS = [g for g, _ in BLOOD_GROUPS]
LOW_UNITS = 5


def _get_or_404(model, pk, **filters):
    """get_object_or_404 that also handles malformed IDs."""
    try:
        return get_object_or_404(model, pk=pk, **filters)
    except ValidationError:
        raise Http404


def verified_bloodbank(view_func):
    """Only verified blood bank accounts may use the management pages."""

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_verified:
            messages.warning(
                request,
                "Your account is awaiting admin verification. "
                "You can manage blood stock once it is verified.",
            )
            return redirect("bloodbank:dashboard")
        return view_func(request, *args, **kwargs)

    return role_required("bloodbank")(wrapper)


def _stock_by_group(user):
    """Total units per blood group for this blood bank."""
    totals = {g: 0 for g in GROUPS}
    for row in BloodInventory.objects.filter(bloodbank=user):
        totals[row.blood_group] = totals.get(row.blood_group, 0) + row.units
    return totals


def _deduct_units(user, group, needed):
    """Remove `needed` units of `group`. Returns False if there isn't enough."""
    rows = list(
        BloodInventory.objects.filter(bloodbank=user, blood_group=group, units__gt=0)
    )
    if sum(r.units for r in rows) < needed:
        return False
    for row in rows:
        take = min(row.units, needed)
        row.units -= take
        row.save(update_fields=["units", "updated_at"])
        needed -= take
        if needed == 0:
            break
    return True


# ---------------------------------------------------------------- dashboard
@role_required("bloodbank")
def dashboard(request):
    stock = _stock_by_group(request.user)
    reqs = BloodRequest.objects.filter(recipient=request.user)
    context = {
        "total_units": sum(stock.values()),
        "low_groups": sum(1 for u in stock.values() if u <= LOW_UNITS),
        "pending": reqs.filter(status="pending").count(),
        "total_requests": reqs.count(),
        "recent_pending": list(
            reqs.filter(status="pending").order_by("-created_at")[:5]
        ),
    }
    return render(request, "bloodbank/dashboard.html", context)


# ---------------------------------------------------------------- inventory
@verified_bloodbank
def inventory(request):
    stock = _stock_by_group(request.user)
    rows = []
    for g in GROUPS:
        units = stock[g]
        level = "out" if units == 0 else "low" if units <= LOW_UNITS else "ok"
        rows.append({"group": g, "units": units, "level": level})
    return render(
        request,
        "bloodbank/inventory.html",
        {"rows": rows, "low_limit": LOW_UNITS},
    )


@verified_bloodbank
@require_POST
def inventory_set(request):
    group = request.POST.get("blood_group", "")
    if group not in GROUPS:
        messages.error(request, "Invalid blood group.")
        return redirect("bloodbank:inventory")
    try:
        units = int(request.POST.get("units", ""))
        if units < 0 or units > 10000:
            raise ValueError
    except ValueError:
        messages.error(request, "Enter a valid number of units (0 to 10000).")
        return redirect("bloodbank:inventory")

    rows = list(BloodInventory.objects.filter(bloodbank=request.user, blood_group=group))
    if rows:
        first = rows[0]
        first.units = units
        first.save(update_fields=["units", "updated_at"])
        for extra in rows[1:]:  # keep one row per blood group
            extra.delete()
    else:
        BloodInventory.objects.create(
            bloodbank=request.user, blood_group=group, units=units
        )
    messages.success(request, f"{group} stock set to {units} units.")
    return redirect("bloodbank:inventory")


# ----------------------------------------------------------------- requests
@verified_bloodbank
def requests_list(request):
    status = request.GET.get("status", "").strip()
    qs = BloodRequest.objects.filter(recipient=request.user)
    if status in dict(BloodRequest.Status.choices):
        qs = qs.filter(status=status)
    return render(
        request,
        "bloodbank/requests.html",
        {
            "requests_list": qs.order_by("-created_at"),
            "current": status,
            "statuses": BloodRequest.Status.choices,
        },
    )


@verified_bloodbank
@require_POST
def request_action(request, pk, action):
    blood_request = _get_or_404(BloodRequest, pk)
    if blood_request.recipient_id != request.user.pk:
        raise Http404

    S = BloodRequest.Status
    who = request.user.organization_name or request.user.username
    link = reverse("patients:my_requests")

    if action == "accept" and blood_request.status == S.PENDING:
        if _deduct_units(
            request.user, blood_request.blood_group, blood_request.units_required
        ):
            blood_request.status = S.ACCEPTED
            blood_request.save(update_fields=["status", "updated_at"])
            messages.success(request, "Request accepted and blood stock updated.")
            notify(
                blood_request.patient,
                f"{who} accepted your {blood_request.blood_group} blood request.",
                link,
            )
        else:
            have = _stock_by_group(request.user)[blood_request.blood_group]
            messages.error(
                request,
                f"Not enough stock: you have {have} units of "
                f"{blood_request.blood_group}, but "
                f"{blood_request.units_required} requested.",
            )
    elif action == "reject" and blood_request.status == S.PENDING:
        blood_request.status = S.REJECTED
        blood_request.save(update_fields=["status", "updated_at"])
        messages.success(request, "Request rejected.")
        notify(
            blood_request.patient,
            f"{who} rejected your {blood_request.blood_group} blood request.",
            link,
        )
    elif action == "fulfil" and blood_request.status == S.ACCEPTED:
        blood_request.status = S.FULFILLED
        blood_request.save(update_fields=["status", "updated_at"])
        messages.success(request, "Request marked as fulfilled.")
        notify(
            blood_request.patient,
            f"Your {blood_request.blood_group} blood request was fulfilled by {who}.",
            link,
        )
    else:
        messages.error(request, "That action isn't allowed for this request.")

    return redirect("bloodbank:requests")