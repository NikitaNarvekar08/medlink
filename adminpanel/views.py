from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from accounts.decorators import role_required
from accounts.models import User
from bloodbank.models import BLOOD_GROUPS, BloodInventory, BloodRequest
from notifications.utils import notify
from pharmacy.models import Medicine, MedicineReservation

GROUPS = [g for g, _ in BLOOD_GROUPS]
ROLE_TABS = [
    ("patient", "Patients"),
    ("pharmacy", "Pharmacies"),
    ("bloodbank", "Blood Banks"),
    ("donor", "Donors"),
]
ORG_ROLES = ["pharmacy", "bloodbank"]  # roles the admin must verify
LOW_STOCK = 10


def _get_or_404(model, pk, **filters):
    """get_object_or_404 that also handles malformed IDs."""
    try:
        return get_object_or_404(model, pk=pk, **filters)
    except ValidationError:
        raise Http404


# ---------------------------------------------------------------- dashboard
@role_required("admin")
def dashboard(request):
    user_stats = [
        {"label": label, "role": role, "value": User.objects.filter(role=role).count()}
        for role, label in ROLE_TABS
    ]
    pending_accounts = list(
        User.objects.filter(role__in=ORG_ROLES, is_verified=False).order_by("-created_at")
    )
    total_units = sum(row.units for row in BloodInventory.objects.all())
    system_stats = [
        {
            "label": "Medicines listed",
            "value": Medicine.objects.count(),
            "url": reverse("adminpanel:medicines"),
        },
        {
            "label": "Pending reservations",
            "value": MedicineReservation.objects.filter(status="pending").count(),
            "url": reverse("adminpanel:reservations") + "?status=pending",
        },
        {
            "label": "Pending blood requests",
            "value": BloodRequest.objects.filter(status="pending").count(),
            "url": reverse("adminpanel:blood_requests") + "?status=pending",
        },
        {
            "label": "Blood units in stock",
            "value": total_units,
            "url": reverse("adminpanel:inventory"),
        },
    ]
    return render(
        request,
        "adminpanel/dashboard.html",
        {
            "user_stats": user_stats,
            "system_stats": system_stats,
            "pending_accounts": pending_accounts,
        },
    )


# -------------------------------------------------------------------- users
@role_required("admin")
def users_list(request):
    role = request.GET.get("role", "").strip()
    view = request.GET.get("view", "").strip()
    q = request.GET.get("q", "").strip()

    qs = User.objects.exclude(role="admin")
    if role in dict(ROLE_TABS):
        qs = qs.filter(role=role)
    if view == "pending":
        qs = qs.filter(role__in=ORG_ROLES, is_verified=False)
    elif view == "inactive":
        qs = qs.filter(is_active=False)
    if q:
        qs = qs.filter(
            Q(username__icontains=q)
            | Q(email__icontains=q)
            | Q(organization_name__icontains=q)
            | Q(city__icontains=q)
        )

    return render(
        request,
        "adminpanel/users.html",
        {
            "users_list": qs.order_by("-created_at"),
            "role": role,
            "view": view,
            "q": q,
            "role_tabs": ROLE_TABS,
        },
    )


@role_required("admin")
@require_POST
def user_action(request, pk, action):
    target = _get_or_404(User, pk)

    if target.pk == request.user.pk or target.role == "admin" or target.is_superuser:
        messages.error(request, "Admin accounts can't be changed from this page.")
    elif action == "verify" and target.role in ORG_ROLES:
        target.is_verified = True
        target.save(update_fields=["is_verified"])
        messages.success(request, f"{target.username} is now verified.")
        notify(
            target,
            "Your account has been verified by the admin. You can now use all features.",
            reverse("dashboard"),
        )
    elif action == "unverify" and target.role in ORG_ROLES:
        target.is_verified = False
        target.save(update_fields=["is_verified"])
        messages.success(request, f"Verification removed from {target.username}.")
        notify(
            target,
            "Your account verification was removed by the admin. Please contact support.",
            reverse("dashboard"),
        )
    elif action == "activate":
        target.is_active = True
        target.save(update_fields=["is_active"])
        messages.success(request, f"{target.username} has been activated.")
    elif action == "deactivate":
        target.is_active = False
        target.save(update_fields=["is_active"])
        messages.success(
            request, f"{target.username} has been deactivated and can no longer log in."
        )
    else:
        messages.error(request, "That action isn't allowed for this account.")

    nxt = request.POST.get("next", "")
    if nxt.startswith("/admin-panel/"):
        return redirect(nxt)
    return redirect("adminpanel:users")


# ---------------------------------------------------------------- medicines
@role_required("admin")
def medicines(request):
    q = request.GET.get("q", "").strip()
    low = request.GET.get("low", "") == "1"
    qs = Medicine.objects.all()
    if q:
        qs = qs.filter(name__icontains=q)
    if low:
        qs = qs.filter(quantity__lte=LOW_STOCK)
    return render(
        request,
        "adminpanel/medicines.html",
        {
            "medicines": qs.order_by("name"),
            "q": q,
            "low": low,
            "low_limit": LOW_STOCK,
        },
    )


# ---------------------------------------------------------------- inventory
@role_required("admin")
def inventory(request):
    banks = list(User.objects.filter(role="bloodbank").order_by("username"))
    per_bank = {}
    group_totals = {g: 0 for g in GROUPS}
    for row in BloodInventory.objects.all():
        units = per_bank.setdefault(row.bloodbank_id, {g: 0 for g in GROUPS})
        units[row.blood_group] = units.get(row.blood_group, 0) + row.units
        group_totals[row.blood_group] = group_totals.get(row.blood_group, 0) + row.units

    matrix = []
    for bank in banks:
        units = per_bank.get(bank.pk, {g: 0 for g in GROUPS})
        matrix.append(
            {
                "bank": bank,
                "cells": [units[g] for g in GROUPS],
                "total": sum(units.values()),
            }
        )

    return render(
        request,
        "adminpanel/inventory.html",
        {
            "groups": GROUPS,
            "matrix": matrix,
            "summary": [{"group": g, "units": group_totals[g]} for g in GROUPS],
            "grand_total": sum(group_totals.values()),
        },
    )


# ------------------------------------------------------------- reservations
@role_required("admin")
def reservations(request):
    status = request.GET.get("status", "").strip()
    qs = MedicineReservation.objects.all()
    if status in dict(MedicineReservation.Status.choices):
        qs = qs.filter(status=status)
    return render(
        request,
        "adminpanel/reservations.html",
        {
            "reservations": qs.order_by("-created_at"),
            "current": status,
            "statuses": MedicineReservation.Status.choices,
        },
    )


# ----------------------------------------------------------- blood requests
@role_required("admin")
def blood_requests(request):
    status = request.GET.get("status", "").strip()
    qs = BloodRequest.objects.all()
    if status in dict(BloodRequest.Status.choices):
        qs = qs.filter(status=status)
    return render(
        request,
        "adminpanel/blood_requests.html",
        {
            "requests_list": qs.order_by("-created_at"),
            "current": status,
            "statuses": BloodRequest.Status.choices,
        },
    )


# ----------------------------------------------------------------- activity
@role_required("admin")
def activity(request):
    events = []
    for u in User.objects.exclude(role="admin").order_by("-created_at")[:15]:
        events.append(
            {
                "time": u.created_at,
                "icon": "👤",
                "text": f"{u.username} registered as {u.get_role_display()}",
                "status": "",
                "label": "",
            }
        )
    for r in MedicineReservation.objects.order_by("-created_at")[:15]:
        events.append(
            {
                "time": r.created_at,
                "icon": "💊",
                "text": f"{r.patient.username} reserved {r.quantity} x "
                f"{r.medicine.name}",
                "status": r.status,
                "label": r.get_status_display(),
            }
        )
    for b in BloodRequest.objects.order_by("-created_at")[:15]:
        events.append(
            {
                "time": b.created_at,
                "icon": "🩸",
                "text": f"{b.patient.username} requested {b.units_required} unit(s) "
                f"of {b.blood_group} from {b.recipient.username}",
                "status": b.status,
                "label": b.get_status_display(),
            }
        )
    events.sort(key=lambda e: e["time"], reverse=True)
    return render(request, "adminpanel/activity.html", {"events": events[:30]})