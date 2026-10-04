from django.contrib import admin

from .models import BloodInventory, BloodRequest


@admin.register(BloodInventory)
class BloodInventoryAdmin(admin.ModelAdmin):
    list_display = ("bloodbank", "blood_group", "units", "updated_at")
    list_filter = ("blood_group",)


@admin.register(BloodRequest)
class BloodRequestAdmin(admin.ModelAdmin):
    list_display = ("patient", "recipient", "blood_group", "units_required", "urgency", "status", "created_at")
    list_filter = ("status", "urgency", "blood_group")