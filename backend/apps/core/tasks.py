import logging

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail

from .models import Notification

logger = logging.getLogger(__name__)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=30, max_retries=5)
def deliver_notification(self, user_ids, event, title, body="", link=""):
    users = get_user_model().objects.filter(pk__in=user_ids, is_active=True)
    url = f"{settings.PORTAL_BASE_URL.rstrip('/')}{link}" if link else ""
    for user in users:
        Notification.objects.get_or_create(
            user=user, event=event, title=title, link=link, is_read=False, defaults={"body": body}
        )
        if user.email:
            try:
                send_mail(title, f"{body}\n\n{url}".strip(), settings.DEFAULT_FROM_EMAIL, [user.email])
            except Exception:
                logger.exception("Ошибка отправки email пользователю %s", user.pk)
