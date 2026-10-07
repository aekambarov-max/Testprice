"""Механизм рассылки запросов КП поставщикам из пула. Ответ поставщика приходит по токену-ссылке
и передаётся обработчику, зарегистрированному модулем-источником (см. register_response_handler)."""

from django.conf import settings
from django.db import transaction

from .models import KpRequest

_RESPONSE_HANDLERS = {}


def register_response_handler(source_type, handler):
    _RESPONSE_HANDLERS[source_type] = handler


def get_response_handler(source_type):
    return _RESPONSE_HANDLERS.get(source_type)


def send_kp_requests(*, source_type, source_id, suppliers, items, sender, subject, message=""):
    created = []
    for supplier in suppliers:
        created.append(
            KpRequest.objects.create(
                supplier=supplier,
                source_type=source_type,
                source_id=str(source_id),
                items=items,
                message=message,
                sent_by=sender,
            )
        )
    ids = [r.pk for r in created]

    def _send():
        from .tasks import email_kp_requests

        try:
            email_kp_requests.delay(ids, subject)
        except Exception:
            import logging

            logging.getLogger(__name__).exception("Не удалось поставить рассылку КП в очередь")

    transaction.on_commit(_send)
    return created


def kp_response_url(kp_request):
    return f"{settings.PORTAL_BASE_URL.rstrip('/')}/kp/{kp_request.token}"
