import logging

from .models import Notification

logger = logging.getLogger(__name__)


def notify(user, message, link=""):
    """Create an in-app notification. Never breaks the calling view."""
    try:
        Notification.objects.create(user=user, message=message[:255], link=link)
    except Exception:
        logger.exception("Could not create notification")