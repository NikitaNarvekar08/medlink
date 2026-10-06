from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from accounts.decorators import role_required
from accounts.models import User
from bloodbank.models import BloodInventory, BloodRequest
from notifications.utils import notify
from pharmacy.models import Medicine, MedicineReservation

from .forms import BloodRequestForm, ReservationForm


def _get_or_404(model, pk):
    """get_object_or_404 that also handles malformed IDs."""
    try:
        return get_object_or_404(model, pk=pk)
    except ValidationError:
        raise Http404


def _same_city(a, b):
    return bool(a) and bool(b) and a.strip().lower() == b.strip().lower()


def _verified_pharmacies(city=""):
    qs = User.objects.filter(role="pharmacy", is_verified=True, is_active=True)
    if city:
        qs = qs.filter(city__icontains=city)
    return list(qs)


def _matching_banks(blood_group, units, city):
    """Verified blood banks that have stock of this group (same city first)."""
    banks = {
        b.pk: b
        for b in User.objects.filter(role="bloodbank", is_verified=True, is_active=True)
    }
    if not banks:
        return []
    rows = BloodInventory.objects.filter(
        bloodbank__in=list(banks.keys()), blood_group=blood_group, units__gt=0
    )
    totals = {}
    for row in rows:
        totals[row.bloodbank_id] = totals.get(row.bloodbank_id, 0) + row.units
    results = [
        {
            "bank": banks[pk],
            "units": total,
            "enough": total >= units,
            "same_city": _same_city(banks[pk].city, city),
        }
        for pk, total in totals.items()
    ]
    return sorted(results, key=lambda r: (not r["same_city"], -r["units"]))


def _matching_donors(blood_group, city):
    """Available donors with the same blood group (same city first)."""
    donors = User.objects.filter(
        role="donor", blood_group=blood_group, is_available=True, is_active=True
    )
    results = [{"donor": d, "same_city": _same_city(d.city, city)} for d in donors]
    return sorted(results, key=lambda r: not r["same_city"])


# ---------------------------------------------------------------- dashboard
@role_required("patient")
def dashboard(request):
    reservations = MedicineReservation.objects.filter(patient=request.user)
    blood = BloodRequest.objects.filter(patient=request.user)
    context = {
        "total_reservations": reservations.count(),
        "pending_reservations": reservations.filter(status="pending").count(),
        "total_blood": blood.count(),
        "pending_blood": blood.filter(status="pending").count(),
    }
    return render(request, "patients/dashboard.html", context)


# ---------------------------------------------------------------- medicines
@role_required("patient")
def medicine_search(request):
    q = request.GET.get("q", "").strip()
    city = request.GET.get("city", "").strip()

    pharmacies = {p.pk: p for p in _verified_pharmacies(city)}
    medicines = []
    if pharmacies:
        qs = Medicine.objects.filter(pharmacy__in=list(pharmacies.keys()))
        if q:
            qs = qs.filter(name__icontains=q)
        medicines = list(qs.order_by("name"))
        for m in medicines:
            m.pharmacy_obj = pharmacies.get(m.pharmacy_id)

    return render(
        request,
        "patients/medicine_search.html",
        {"medicines": medicines, "q": q, "city": city},
    )


@role_required("patient")
def medicine_detail(request, pk):
    medicine = _get_or_404(Medicine, pk)
    pharmacy = medicine.pharmacy
    if not (pharmacy.is_verified and pharmacy.is_active):
        raise Http404

    if request.method == "POST":
        form = ReservationForm(request.POST)
        if medicine.quantity <= 0:
            messages.error(request, "Sorry, this medicine is out of stock.")
        elif form.is_valid():
            qty = form.cleaned_data["quantity"]
            if qty > medicine.quantity:
                form.add_error(
                    "quantity", f"Only {medicine.quantity} units are available."
                )
            else:
                MedicineReservation.objects.create(
                    patient=request.user,
                    medicine=medicine,
                    quantity=qty,
                    note=form.cleaned_data["note"],
                    status=MedicineReservation.Status.PENDING,
                )
                notify(
                    pharmacy,
                    f"New reservation: {request.user.username} reserved "
                    f"{qty} x {medicine.name}.",
                    reverse("pharmacy:reservations"),
                )
                messages.success(
                    request,
                    "Reservation request sent. The pharmacy will accept or reject it.",
                )
                return redirect("patients:my_requests")
    else:
        form = ReservationForm()

    return render(
        request,
        "patients/medicine_detail.html",
        {"medicine": medicine, "pharmacy": pharmacy, "form": form},
    )


# -------------------------------------------------------------------- blood
@role_required("patient")
def blood_request(request):
    form = BloodRequestForm(request.GET or None, initial={"city": request.user.city})
    context = {"form": form, "searched": False}

    if request.GET and form.is_valid():
        data = form.cleaned_data
        context.update(
            searched=True,
            params=data,
            banks=_matching_banks(data["blood_group"], data["units"], data["city"]),
            donors=_matching_donors(data["blood_group"], data["city"]),
        )
    return render(request, "patients/blood_request.html", context)


@role_required("patient")
def blood_send(request):
    """Create a blood request addressed to one blood bank or donor."""
    if request.method != "POST":
        return redirect("patients:blood_request")

    form = BloodRequestForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Invalid request details. Please try again.")
        return redirect("patients:blood_request")
    data = form.cleaned_data

    recipient = _get_or_404(User, request.POST.get("recipient_id"))
    if recipient.role == "bloodbank":
        valid = recipient.is_verified and recipient.is_active
    elif recipient.role == "donor":
        valid = (
            recipient.is_active
            and recipient.is_available
            and recipient.blood_group == data["blood_group"]
        )
    else:
        valid = False
    if not valid:
        messages.error(request, "This blood bank or donor is no longer available.")
        return redirect("patients:blood_request")

    already_sent = BloodRequest.objects.filter(
        patient=request.user,
        recipient=recipient,
        blood_group=data["blood_group"],
        status=BloodRequest.Status.PENDING,
    ).exists()
    if already_sent:
        messages.warning(
            request, "You already have a pending request to them for this blood group."
        )
        return redirect("patients:my_requests")

    BloodRequest.objects.create(
        patient=request.user,
        recipient=recipient,
        blood_group=data["blood_group"],
        units_required=data["units"],
        hospital_name=data["hospital_name"],
        city=data["city"],
        urgency=data["urgency"],
        note=data["note"],
        status=BloodRequest.Status.PENDING,
    )

    link = (
        reverse("bloodbank:requests")
        if recipient.role == "bloodbank"
        else reverse("donors:requests")
    )
    notify(
        recipient,
        f"New {data['blood_group']} blood request from {request.user.username} "
        f"({data['units']} unit(s)) at {data['hospital_name']}.",
        link,
    )

    messages.success(request, "Blood request sent. You can track it here.")
    return redirect("patients:my_requests")


# ----------------------------------------------------------------- tracking
@role_required("patient")
def my_requests(request):
    reservations = MedicineReservation.objects.filter(
        patient=request.user
    ).order_by("-created_at")
    blood_requests = BloodRequest.objects.filter(
        patient=request.user
    ).order_by("-created_at")
    return render(
        request,
        "patients/my_requests.html",
        {"reservations": reservations, "blood_requests": blood_requests},
    )