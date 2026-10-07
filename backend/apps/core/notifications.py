"""Сервис уведомлений: в системе + email. Отправка асинхронная (Celery), после коммита транзакции,
поэтому ошибка доставки никогда не откатывает смену статуса документа."""

import logging

from django.db import transaction

logger = logging.getLogger(__name__)


def notify(users, event, title, body="", link=""):
    user_ids = sorted({u.pk for u in users if u is not None and u.is_active})
    if not user_ids:
        return

    def _send():
        from .tasks import deliver_notification

        try:
            deliver_notification.delay(user_ids, event, title, body, link)
        except Exception:  # брокер недоступен — статус уже сохранён, просто логируем
            logger.exception("Не удалось поставить уведомление %s в очередь", event)

    transaction.on_commit(_send)
