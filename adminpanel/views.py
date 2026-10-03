from django.shortcuts import render

from accounts.decorators import role_required
from accounts.models import User


@role_required("admin")
def dashboard(request):
    stats = [
        ("Patients", User.objects.filter(role="patient").count()),
        ("Pharmacies", User.objects.filter(role="pharmacy").count()),
        ("Blood Banks", User.objects.filter(role="bloodbank").count()),
        ("Donors", User.objects.filter(role="donor").count()),
        ("Pending Verification", User.objects.filter(is_verified=False).exclude(role="admin").count()),
    ]
    return render(request, "adminpanel/dashboard.html", {"stats": stats})