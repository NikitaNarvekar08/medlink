from django.urls import path

from . import views

app_name = "donors"

urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
    path("availability/", views.toggle_availability, name="toggle_availability"),
    path("profile/", views.profile, name="profile"),
    path("requests/", views.requests_list, name="requests"),
    path(
        "requests/<str:pk>/<str:action>/",
        views.request_action,
        name="request_action",
    ),
]