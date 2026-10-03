from django.apps import AppConfig


class ChatbotConfig(AppConfig):
    default_auto_field = 'django_mongodb_backend.fields.ObjectIdAutoField'
    name = 'chatbot'
