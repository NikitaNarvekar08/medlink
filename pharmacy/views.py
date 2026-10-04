from functools import wraps

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.decorators import role_required

from .forms import MedicineForm
from .models import Medicine, MedicineReservation

LOW_STOCK_LIMIT = 10


def _get_or_404(model, pk, **filters):
    """get_object_or_404 that also handles malformed IDs."""
    try:
        return get_object_or_404(model, pk=pk, **filters)
    except ValidationError:
        raise Http404


def verified_pharmacy(view_func):
    """Only verified pharmacy accounts may use the management pages."""

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_verified:
            messages.warning(
                request,
                "Your account is awaiting admin verification. "
                "You can manage medicines once it is verified.",
            )
            return redirect("pharmacy:dashboard")
        return view_func(request, *args, **kwargs)

    return role_required("pharmacy")(wrapper)


def _my_reservations(user):
    medicine_ids = list(
        Medicine.objects.filter(pharmacy=user).values_list("pk", flat=True)
    )
    return MedicineReservation.objects.filter(medicine__in=medicine_ids)


# ---------------------------------------------------------------- dashboard
@role_required("pharmacy")
def dashboard(request):
    medicines = Medicine.objects.filter(pharmacy=request.user)
    reservations = _my_reservations(request.user)
    context = {
        "total_medicines": medicines.count(),
        "low_stock": medicines.filter(quantity__lte=LOW_STOCK_LIMIT).count(),
        "pending": reservations.filter(status="pending").count(),
        "total_reservations": reservations.count(),
        "recent_pending": list(
            reservations.filter(status="pending").order_by("-created_at")[:5]
        ),
    }
    return render(request, "pharmacy/dashboard.html", context)


# ---------------------------------------------------------------- medicines
@verified_pharmacy
def medicine_list(request):
    q = request.GET.get("q", "").strip()
    medicines = Medicine.objects.filter(pharmacy=request.user)
    if q:
        medicines = medicines.filter(name__icontains=q)
    return render(
        request,
        "pharmacy/medicine_list.html",
        {"medicines": medicines.order_by("name"), "q": q, "low_limit": LOW_STOCK_LIMIT},
    )


@verified_pharmacy
def medicine_add(request):
    form = MedicineForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        medicine = form.save(commit=False)
        medicine.pharmacy = request.user
        medicine.save()
        messages.success(request, f"{medicine.name} added to your stock.")
        return redirect("pharmacy:medicine_list")
    return render(
        request,
        "pharmacy/medicine_form.html",
        {"form": form, "heading": "Add medicine", "button": "SAVE MEDICINE"},
    )


@verified_pharmacy
def medicine_edit(request, pk):
    medicine = _get_or_404(Medicine, pk, pharmacy=request.user)
    form = MedicineForm(request.POST or None, instance=medicine)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"{medicine.name} updated.")
        return redirect("pharmacy:medicine_list")
    return render(
        request,
        "pharmacy/medicine_form.html",
        {"form": form, "heading": f"Edit {medicine.name}", "button": "UPDATE MEDICINE"},
    )


@verified_pharmacy
@require_POST
def medicine_delete(request, pk):
    medicine = _get_or_404(Medicine, pk, pharmacy=request.user)
    name = medicine.name
    medicine.delete()
    messages.success(request, f"{name} deleted.")
    return redirect("pharmacy:medicine_list")


@verified_pharmacy
@require_POST
def update_stock(request, pk):
    medicine = _get_or_404(Medicine, pk, pharmacy=request.user)
    try:
        qty = int(request.POST.get("quantity", ""))
        if qty < 0:
            raise ValueError
    except ValueError:
        messages.error(request, "Enter a valid stock quantity (0 or more).")
        return redirect("pharmacy:medicine_list")
    medicine.quantity = qty
    medicine.save(update_fields=["quantity", "updated_at"])
    messages.success(request, f"Stock of {medicine.name} set to {qty}.")
    return redirect("pharmacy:medicine_list")


# ------------------------------------------------------------- reservations
@verified_pharmacy
def reservations(request):
    status = request.GET.get("status", "").strip()
    qs = _my_reservations(request.user)
    if status in dict(MedicineReservation.Status.choices):
        qs = qs.filter(status=status)
    return render(
        request,
        "pharmacy/reservations.html",
        {
            "reservations": qs.order_by("-created_at"),
            "current": status,
            "statuses": MedicineReservation.Status.choices,
        },
    )


@verified_pharmacy
@require_POST
def reservation_action(request, pk, action):
    reservation = _get_or_404(MedicineReservation, pk)
    medicine = reservation.medicine
    if medicine.pharmacy_id != request.user.pk:
        raise Http404

    S = MedicineReservation.Status

    if action == "accept" and reservation.status == S.PENDING:
        if reservation.quantity > medicine.quantity:
            messages.error(
                request,
                f"Not enough stock: only {medicine.quantity} units of "
                f"{medicine.name} left, but {reservation.quantity} requested.",
            )
        else:
            medicine.quantity -= reservation.quantity
            medicine.save(update_fields=["quantity", "updated_at"])
            reservation.status = S.ACCEPTED
            reservation.save(update_fields=["status", "updated_at"])
            messages.success(
                request, "Reservation accepted and stock updated."
            )
    elif action == "reject" and reservation.status == S.PENDING:
        reservation.status = S.REJECTED
        reservation.save(update_fields=["status", "updated_at"])
        messages.success(request, "Reservation rejected.")
    elif action == "complete" and reservation.status == S.ACCEPTED:
        reservation.status = S.COMPLETED
        reservation.save(update_fields=["status", "updated_at"])
        messages.success(request, "Reservation marked as completed.")
    else:
        messages.error(request, "That action isn't allowed for this reservation.")

    return redirect("pharmacy:reservations")