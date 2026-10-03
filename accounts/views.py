from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render

from .forms import LoginForm, RegisterForm

ROLE_DASHBOARDS = {
    "patient": "patients:dashboard",
    "pharmacy": "pharmacy:dashboard",
    "bloodbank": "bloodbank:dashboard",
    "donor": "donors:dashboard",
    "admin": "adminpanel:dashboard",
}


def home(request):
    return render(request, "home.html")


def about(request):
    return render(request, "about.html")


def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful. Welcome to MedLink!")
            return redirect("dashboard")
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {"form": form})


class CustomLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True


@login_required
def dashboard_redirect(request):
    """Send each user to the dashboard for their role."""
    return redirect(ROLE_DASHBOARDS.get(request.user.role, "home"))