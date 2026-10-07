"""Формирование PDF «Маркетинговое заключение» (HTML-шаблон Django + WeasyPrint, без внешних сервисов)."""

from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone

from apps.core.models import full_name
from apps.core.roles import ROLE_TITLES

from .models import ApprovalStep, Stage


def build_context(analysis):
    steps = (analysis.steps.filter(iteration=analysis.iteration, status=ApprovalStep.StepStatus.APPROVED)
             .select_related("assignee_user").order_by("stage", "order"))
    offers = analysis.offers.prefetch_related("prices__item").order_by("supplier_name", "offer_date")
    author_profile = getattr(analysis.author, "profile", None)
    approval_rows = []
    for step in steps:
        approval_rows.append({
            "stage": Stage(step.stage).label,
            "name": step.decided_by_name,
            "position": step.decided_by_position or ROLE_TITLES.get(step.assignee_role, ""),
            "decision": "Утверждено" if step.stage == Stage.DIRECTOR else "Согласовано",
            "decided_at": timezone.localtime(step.decided_at),
            "comment": step.comment,
        })
    final = next((r for r in approval_rows if r["decision"] == "Утверждено"), None)
    return {
        "analysis": analysis,
        "items": analysis.items.all(),
        "offers": offers,
        "approval_rows": approval_rows,
        "final": final,
        "author_name": full_name(analysis.author),
        "author_position": author_profile.position if author_profile else "",
        "approved_at": timezone.localtime(analysis.approved_at),
        "vat_rate": settings.VAT_RATE_PERCENT,
        "calc_method": {"average": "среднее арифметическое цен КП", "min": "минимальная цена КП"}.get(
            settings.MA_PRICE_CALC_METHOD, settings.MA_PRICE_CALC_METHOD),
        "fonts_dir": (settings.BASE_DIR / "static" / "fonts").as_uri(),
        "logo": (settings.BASE_DIR / "static" / "img" / "kmg_logo.svg").as_uri(),
    }


def render_conclusion_pdf(analysis):
    from weasyprint import HTML

    html = render_to_string("marketing_analysis/conclusion.html", build_context(analysis))
    return HTML(string=html, base_url=str(settings.BASE_DIR)).write_pdf()
