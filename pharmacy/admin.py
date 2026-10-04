from django.contrib import admin

from .models import Medicine, MedicineReservation


@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ("name", "pharmacy", "price", "quantity")
    search_fields = ("name",)


@admin.register(MedicineReservation)
class MedicineReservationAdmin(admin.ModelAdmin):
    list_display = ("patient", "medicine", "quantity", "status", "created_at")
    list_filter = ("status",)