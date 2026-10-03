from django.apps import AppConfig


class BloodbankConfig(AppConfig):
    default_auto_field = 'django_mongodb_backend.fields.ObjectIdAutoField'
    name = 'bloodbank'
