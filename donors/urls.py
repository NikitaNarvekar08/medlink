from django.urls import path

from . import views

app_name = "donors"

urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
]