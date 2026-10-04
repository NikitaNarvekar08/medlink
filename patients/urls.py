from django.urls import path

from . import views

app_name = "patients"

urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
    path("medicines/", views.medicine_search, name="medicine_search"),
    path("medicines/<str:pk>/", views.medicine_detail, name="medicine_detail"),
    path("blood/", views.blood_request, name="blood_request"),
    path("blood/send/", views.blood_send, name="blood_send"),
    path("requests/", views.my_requests, name="my_requests"),
]