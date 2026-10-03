from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("accounts.urls")),
    path("patient/", include("patients.urls")),
    path("pharmacy/", include("pharmacy.urls")),
    path("bloodbank/", include("bloodbank.urls")),
    path("donor/", include("donors.urls")),
    path("admin-panel/", include("adminpanel.urls")),
]