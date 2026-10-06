from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from accounts.decorators import role_required
from bloodbank.models import BloodRequest
from notifications.utils import notify

from .forms import DonorProfileForm


def _get_or_404(model, pk, **filters):
    """get_object_or_404 that also handles malformed IDs."""
    try:
        return get_object_or_404(model, pk=pk, **filters)
    except ValidationError:
        raise Http404


# ---------------------------------------------------------------- dashboard
@role_required("donor")
def dashboard(request):
    reqs = BloodRequest.objects.filter(recipient=request.user)
    context = {
        "total_requests": reqs.count(),
        "pending": reqs.filter(status="pending").count(),
        "accepted": reqs.filter(status="accepted").count(),
        "fulfilled": reqs.filter(status="fulfilled").count(),
        "recent_pending": list(
            reqs.filter(status="pending").order_by("-created_at")[:5]
        ),
    }
    return render(request, "donors/dashboard.html", context)


@role_required("donor")
@require_POST
def toggle_availability(request):
    request.user.is_available = not request.user.is_available
    request.user.save(update_fields=["is_available"])
    if request.user.is_available:
        messages.success(request, "You are now marked as available to donate.")
    else:
        messages.success(request, "You are now marked as unavailable.")
    return redirect("donors:dashboard")


# ------------------------------------------------------------------ profile
@role_required("donor")
def profile(request):
    form = DonorProfileForm(request.POST or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Your profile has been updated.")
        return redirect("donors:profile")
    return render(request, "donors/profile.html", {"form": form})


# ----------------------------------------------------------------- requests
@role_required("donor")
def requests_list(request):
    status = request.GET.get("status", "").strip()
    qs = BloodRequest.objects.filter(recipient=request.user)
    if status in dict(BloodRequest.Status.choices):
        qs = qs.filter(status=status)
    return render(
        request,
        "donors/requests.html",
        {
            "requests_list": qs.order_by("-created_at"),
            "current": status,
            "statuses": BloodRequest.Status.choices,
        },
    )


@role_required("donor")
@require_POST
def request_action(request, pk, action):
    blood_request = _get_or_404(BloodRequest, pk)
    if blood_request.recipient_id != request.user.pk:
        raise Http404

    S = BloodRequest.Status
    who = request.user.username
    link = reverse("patients:my_requests")

    if action == "accept" and blood_request.status == S.PENDING:
        if blood_request.blood_group != request.user.blood_group:
            messages.error(
                request,
                "This request is for a different blood group than the one "
                "on your profile.",
            )
        elif not request.user.is_available:
            messages.error(
                request,
                "You are marked as unavailable. Turn availability on before accepting.",
            )
        else:
            blood_request.status = S.ACCEPTED
            blood_request.save(update_fields=["status", "updated_at"])
            messages.success(
                request, "Request accepted. The patient can now see your phone number."
            )
            notify(
                blood_request.patient,
                f"Donor {who} accepted your {blood_request.blood_group} blood request.",
                link,
            )
    elif action == "reject" and blood_request.status == S.PENDING:
        blood_request.status = S.REJECTED
        blood_request.save(update_fields=["status", "updated_at"])
        messages.success(request, "Request rejected.")
        notify(
            blood_request.patient,
            f"Donor {who} could not accept your {blood_request.blood_group} request.",
            link,
        )
    elif action == "fulfil" and blood_request.status == S.ACCEPTED:
        blood_request.status = S.FULFILLED
        blood_request.save(update_fields=["status", "updated_at"])
        messages.success(request, "Marked as fulfilled. Thank you for donating!")
        notify(
            blood_request.patient,
            f"Donor {who} marked your {blood_request.blood_group} request as fulfilled.",
            link,
        )
    else:
        messages.error(request, "That action isn't allowed for this request.")

    return redirect("donors:requests")