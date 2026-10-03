from django.apps import AppConfig


class AdminpanelConfig(AppConfig):
    default_auto_field = 'django_mongodb_backend.fields.ObjectIdAutoField'
    name = 'adminpanel'
