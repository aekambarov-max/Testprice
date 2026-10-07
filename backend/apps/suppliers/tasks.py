import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

from .models import KpRequest
from .services import kp_response_url

logger = logging.getLogger(__name__)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=60, max_retries=5)
def email_kp_requests(self, request_ids, subject):
    for req in KpRequest.objects.filter(pk__in=request_ids).select_related("supplier"):
        if not req.supplier.email:
            continue
        lines = [f"Уважаемые коллеги, просим направить коммерческое предложение по позициям:", ""]
        for item in req.items:
            lines.append(f"- {item.get('nsi_code', '')} {item.get('name', '')}: {item.get('quantity', '')} {item.get('unit', '')}")
        if req.message:
            lines += ["", req.message]
        lines += ["", f"Подать КП онлайн: {kp_response_url(req)}"]
        send_mail(subject, "\n".join(lines), settings.DEFAULT_FROM_EMAIL, [req.supplier.email])
