from django.shortcuts import render

from accounts.decorators import role_required


@role_required("pharmacy")
def dashboard(request):
    return render(request, "pharmacy/dashboard.html")