from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Single user model for all MedLink roles."""

    class Role(models.TextChoices):
        PATIENT = "patient", "Patient"
        PHARMACY = "pharmacy", "Pharmacy"
        BLOODBANK = "bloodbank", "Blood Bank"
        DONOR = "donor", "Donor"
        ADMIN = "admin", "Admin"

    BLOOD_GROUPS = [
        (g, g) for g in ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
    ]

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.PATIENT)
    phone = models.CharField(max_length=15, blank=True)
    city = models.CharField(max_length=100, blank=True)
    address = models.CharField(max_length=255, blank=True)

    # Used by pharmacies and blood banks
    organization_name = models.CharField(max_length=150, blank=True)
    license_number = models.CharField(max_length=50, blank=True)

    # Used by donors
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUPS, blank=True)
    is_available = models.BooleanField(default=True)

    # Admin verifies pharmacy / blood bank accounts
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "users"

    def save(self, *args, **kwargs):
        # Superusers created with createsuperuser are always admins
        if self.is_superuser:
            self.role = self.Role.ADMIN
            self.is_verified = True
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.role})"