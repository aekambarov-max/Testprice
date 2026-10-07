import hashlib
import logging

from celery import shared_task
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone

from apps.core.notifications import notify

from .models import MarketingAnalysis, PdfStatus, Status
from .pdf import render_conclusion_pdf
from .signing import sign_conclusion

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_conclusion_pdf(self, analysis_id):
    """Формирует заключение после утверждения. Файл неизменяем: если уже сформирован — ничего не делает."""
    try:
        with transaction.atomic():
            analysis = MarketingAnalysis.objects.select_for_update().get(pk=analysis_id)
            if analysis.status != Status.APPROVED or analysis.pdf_status == PdfStatus.READY:
                return analysis.pdf_sha256
            pdf_bytes = sign_conclusion(analysis, render_conclusion_pdf(analysis))
            sha256 = hashlib.sha256(pdf_bytes).hexdigest()
            analysis.pdf_file.save(f"Маркетинговое_заключение_{analysis.number}.pdf", ContentFile(pdf_bytes),
                                   save=False)
            analysis.pdf_sha256 = sha256
            analysis.pdf_status = PdfStatus.READY
            analysis.pdf_generated_at = timezone.now()
            analysis.save(update_fields=["pdf_file", "pdf_sha256", "pdf_status", "pdf_generated_at"])
            recipients = [analysis.author] + ([analysis.initiator_user] if analysis.initiator_user else [])
            notify(recipients, "ma_pdf_ready", f"Маркетинговое заключение {analysis.number} сформировано",
                   "Заключение доступно для скачивания в карточке анализа.", f"/marketing-analyses/{analysis.pk}")
        return sha256
    except Exception as exc:
        logger.exception("Ошибка формирования PDF для анализа %s", analysis_id)
        if self.request.retries >= self.max_retries or self.request.is_eager:
            MarketingAnalysis.objects.filter(pk=analysis_id).exclude(pdf_status=PdfStatus.READY).update(
                pdf_status=PdfStatus.FAILED)
            if self.request.is_eager:
                return None
            raise
        raise self.retry(exc=exc)
