from django.shortcuts import render

from accounts.decorators import role_required


@role_required("bloodbank")
def dashboard(request):
    return render(request, "bloodbank/dashboard.html")