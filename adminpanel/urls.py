from django.urls import path

from . import views

app_name = "adminpanel"

urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
    path("users/", views.users_list, name="users"),
    path("users/<str:pk>/<str:action>/", views.user_action, name="user_action"),
    path("medicines/", views.medicines, name="medicines"),
    path("inventory/", views.inventory, name="inventory"),
    path("reservations/", views.reservations, name="reservations"),
    path("blood-requests/", views.blood_requests, name="blood_requests"),
    path("activity/", views.activity, name="activity"),
]