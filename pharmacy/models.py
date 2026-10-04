from django.conf import settings
from django.db import models


class Medicine(models.Model):
    pharmacy = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="medicines",
        limit_choices_to={"role": "pharmacy"},
    )
    name = models.CharField(max_length=150)
    category = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    quantity = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "medicines"
        ordering = ["name"]

    @property
    def is_available(self):
        return self.quantity > 0

    def __str__(self):
        return f"{self.name} ({self.pharmacy.username})"


class MedicineReservation(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        REJECTED = "rejected", "Rejected"
        COMPLETED = "completed", "Completed"

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="medicine_reservations",
    )
    medicine = models.ForeignKey(
        Medicine, on_delete=models.CASCADE, related_name="reservations"
    )
    quantity = models.PositiveIntegerField(default=1)
    note = models.CharField(max_length=255, blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "medicine_reservations"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.patient.username} - {self.medicine.name} ({self.status})"