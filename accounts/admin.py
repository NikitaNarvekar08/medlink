from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "role", "is_verified", "is_active")
    list_filter = ("role", "is_verified", "is_active")
    fieldsets = UserAdmin.fieldsets + (
        (
            "MedLink details",
            {
                "fields": (
                    "role", "phone", "city", "address",
                    "organization_name", "license_number",
                    "blood_group", "is_available", "is_verified",
                )
            },
        ),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("MedLink details", {"fields": ("role", "phone", "city")}),
    )