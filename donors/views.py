from django.shortcuts import render

from accounts.decorators import role_required


@role_required("donor")
def dashboard(request):
    return render(request, "donors/dashboard.html")