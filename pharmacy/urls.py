from django.urls import path

from . import views

app_name = "pharmacy"

urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
    path("medicines/", views.medicine_list, name="medicine_list"),
    path("medicines/add/", views.medicine_add, name="medicine_add"),
    path("medicines/<str:pk>/edit/", views.medicine_edit, name="medicine_edit"),
    path("medicines/<str:pk>/delete/", views.medicine_delete, name="medicine_delete"),
    path("medicines/<str:pk>/stock/", views.update_stock, name="update_stock"),
    path("reservations/", views.reservations, name="reservations"),
    path(
        "reservations/<str:pk>/<str:action>/",
        views.reservation_action,
        name="reservation_action",
    ),
]