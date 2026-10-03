from django.apps import AppConfig


class PharmacyConfig(AppConfig):
    default_auto_field = 'django_mongodb_backend.fields.ObjectIdAutoField'
    name = 'pharmacy'
