from django.shortcuts import render

from accounts.decorators import role_required


@role_required("patient")
def dashboard(request):
    return render(request, "patients/dashboard.html")