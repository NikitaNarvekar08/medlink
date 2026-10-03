from django.urls import path

from . import views

app_name = "bloodbank"

urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
]