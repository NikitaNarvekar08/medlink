from django.urls import path

from . import views

app_name = "bloodbank"

urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
    path("inventory/", views.inventory, name="inventory"),
    path("inventory/set/", views.inventory_set, name="inventory_set"),
    path("requests/", views.requests_list, name="requests"),
    path(
        "requests/<str:pk>/<str:action>/",
        views.request_action,
        name="request_action",
    ),
]