from django.conf import settings
from django.db import models

BLOOD_GROUPS = [(g, g) for g in ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]]


class BloodInventory(models.Model):
    bloodbank = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="inventory",
        limit_choices_to={"role": "bloodbank"},
    )
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUPS)
    units = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "blood_inventory"
        ordering = ["blood_group"]

    @property
    def is_available(self):
        return self.units > 0

    def __str__(self):
        return f"{self.bloodbank.username} - {self.blood_group}: {self.units}"


class BloodRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        REJECTED = "rejected", "Rejected"
        FULFILLED = "fulfilled", "Fulfilled"

    class Urgency(models.TextChoices):
        NORMAL = "normal", "Normal"
        URGENT = "urgent", "Urgent"
        CRITICAL = "critical", "Critical"

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="blood_requests",
    )
    # The blood bank or donor this request is sent to
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_blood_requests",
    )
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUPS)
    units_required = models.PositiveIntegerField(default=1)
    hospital_name = models.CharField(max_length=150)
    city = models.CharField(max_length=100)
    urgency = models.CharField(
        max_length=10, choices=Urgency.choices, default=Urgency.NORMAL
    )
    note = models.CharField(max_length=255, blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "blood_requests"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.patient.username} needs {self.blood_group} ({self.status})"