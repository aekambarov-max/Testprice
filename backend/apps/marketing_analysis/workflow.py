"""State machine маркетингового анализа (раздел 3 ТЗ).

Все смены статуса выполняются только здесь: в транзакции, с блокировкой строки (select_for_update),
проверкой ожидаемого текущего статуса, проверкой прав исполнителя и записью в журнал аудита.
"""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied

from apps.core import roles
from apps.core.exceptions import BusinessError, ConflictError
from apps.core.models import full_name
from apps.core.notifications import notify
from apps.core.services import audit
from apps.pricing.models import PriceCatalogEntry

from . import access
from .models import (
    EDITABLE_STATUSES,
    ON_APPROVAL_STATUSES,
    STAGE_STATUS,
    ApprovalStep,
    MarketingAnalysis,
    PdfStatus,
    Stage,
    Status,
)

S = Status
TRANSITIONS = {
    S.DRAFT: {S.COLLECTING_KP, S.CANCELLED},
    # TODO(PO): аннулирование из «Сбор КП» в таблице ТЗ не указано, но статус редактируемый — разрешено.
    S.COLLECTING_KP: {S.ON_APPROVAL_DZO, S.ON_APPROVAL_DB, S.CANCELLED},
    S.ON_APPROVAL_DZO: {S.ON_APPROVAL_DB, S.REWORK},
    S.ON_APPROVAL_DB: {S.ON_FINAL_APPROVAL, S.REWORK},
    S.ON_FINAL_APPROVAL: {S.APPROVED, S.REWORK},
    # rework → on_final_approval возможен только при MA_RESTART_ROUTE_FROM_BEGINNING=False (возврат директором).
    S.REWORK: {S.ON_APPROVAL_DZO, S.ON_APPROVAL_DB, S.ON_FINAL_APPROVAL, S.CANCELLED},
    S.APPROVED: set(),
    S.CANCELLED: set(),
}

STAGE_ROLES = {Stage.DB: roles.DB_SPECIALIST, Stage.DIRECTOR: roles.DB_DIRECTOR}


def lock(analysis_id, expected_statuses):
    """Блокирует строку анализа и проверяет ожидаемый статус (защита от гонок и двойного нажатия)."""
    analysis = MarketingAnalysis.objects.select_for_update().get(pk=analysis_id)
    if analysis.status not in expected_statuses:
        raise ConflictError(
            "status_changed",
            f"Действие недоступно: анализ уже в статусе «{analysis.get_status_display()}». Обновите страницу.",
        )
    return analysis


def _transition(analysis, to_status, *, user, request=None, action, comment="", payload=None):
    from_status = analysis.status
    if to_status not in TRANSITIONS[from_status]:
        raise BusinessError("transition_forbidden", f"Переход {from_status} → {to_status} запрещён")
    analysis.status = to_status
    analysis.save()
    audit(analysis, action, user=user, request=request, from_status=from_status, to_status=to_status,
          comment=comment, payload=payload)


def _link(analysis):
    return f"/marketing-analyses/{analysis.pk}"


def step_executors(step):
    if step.assignee_user_id:
        return [step.assignee_user]
    return list(get_user_model().objects.filter(groups__name=step.assignee_role, is_active=True))


def _notify_step(analysis, step):
    notify(
        step_executors(step),
        "ma_step_assigned",
        f"Маркетинговый анализ {analysis.number} ожидает вашего решения",
        f"Этап: {Stage(step.stage).label}. ДЗО: {analysis.dzo.name_ru}.",
        _link(analysis),
    )


def start_collecting(analysis_id, *, user, request=None, action="collecting_started"):
    with transaction.atomic():
        analysis = lock(analysis_id, [S.DRAFT])
        if not access.can_edit(user, analysis):
            raise PermissionDenied()
        _transition(analysis, S.COLLECTING_KP, user=user, request=request, action=action)
    return analysis


def validate_for_submit(analysis):
    errors = []
    if not analysis.initiator_display:
        errors.append({"field": "initiator", "code": "initiator_required", "message": "Не указан инициатор потребности"})
    if not analysis.dzo_id:
        errors.append({"field": "dzo", "code": "dzo_required", "message": "Не указано ДЗО"})
    items = list(analysis.items.prefetch_related("offer_prices"))
    if not items:
        errors.append({"field": "items", "code": "items_required", "message": "Добавьте хотя бы одну позицию"})
    min_kp = settings.MA_MIN_KP_COUNT
    for item in items:
        kp_count = len(item.offer_prices.all())
        if kp_count < min_kp:
            errors.append({
                "field": "offers", "item_id": item.pk, "code": "not_enough_offers",
                "message": f"Позиция {item.line_no} ({item.name}): загружено КП {kp_count}, требуется не менее {min_kp}",
            })
        if item.marketing_price is None:
            errors.append({
                "field": "calculation", "item_id": item.pk, "code": "price_not_calculated",
                "message": f"Позиция {item.line_no} ({item.name}): не рассчитана маркетинговая цена",
            })
    if not analysis.approvers.exists() and not settings.MA_ALLOW_SKIP_DZO_STAGE:
        if not (analysis.status == S.REWORK and not settings.MA_RESTART_ROUTE_FROM_BEGINNING
                and (analysis.returned_from_stage or 1) > Stage.DZO):
            errors.append({"field": "approvers", "code": "approvers_required",
                           "message": "Выберите хотя бы одного согласующего этапа 1"})
    return errors


def submit(analysis_id, *, user, request=None):
    with transaction.atomic():
        analysis = lock(analysis_id, [S.COLLECTING_KP, S.REWORK])
        if not access.can_edit(user, analysis):
            raise PermissionDenied()
        errors = validate_for_submit(analysis)
        if errors:
            raise BusinessError("validation_failed", "Анализ не готов к отправке на согласование", errors=errors)

        start = Stage.DZO
        if analysis.status == S.REWORK and not settings.MA_RESTART_ROUTE_FROM_BEGINNING and analysis.returned_from_stage:
            start = Stage(analysis.returned_from_stage)
        approvers = list(analysis.approvers.select_related("user"))
        if start == Stage.DZO and not approvers:
            start = Stage.DB  # допустимо только при MA_ALLOW_SKIP_DZO_STAGE (проверено в validate_for_submit)

        analysis.iteration += 1
        steps = []
        if start == Stage.DZO:
            for approver in approvers:
                steps.append(ApprovalStep(analysis=analysis, iteration=analysis.iteration, stage=Stage.DZO,
                                          order=approver.order, assignee_user=approver.user))
        for stage in (Stage.DB, Stage.DIRECTOR):
            if stage >= start:
                # TODO(PO): вопрос 5 — назначение конкретного специалиста ДБ КМГ (MA_DB_STAGE_ASSIGNMENT) и SLA.
                steps.append(ApprovalStep(analysis=analysis, iteration=analysis.iteration, stage=stage,
                                          order=1, assignee_role=STAGE_ROLES[stage]))
        first = steps[0]
        first.status = ApprovalStep.StepStatus.PENDING
        first.activated_at = timezone.now()
        ApprovalStep.objects.bulk_create(steps)

        analysis.current_stage = first.stage
        analysis.submitted_at = timezone.now()
        analysis.returned_from_stage = None
        _transition(analysis, STAGE_STATUS[Stage(first.stage)], user=user, request=request, action="submitted",
                    payload={"iteration": analysis.iteration, "start_stage": int(start)})
        first = analysis.steps.get(iteration=analysis.iteration, status=ApprovalStep.StepStatus.PENDING)
        _notify_step(analysis, first)
    return analysis


def decide(analysis_id, *, user, decision, comment="", step_id=None, request=None):
    comment = (comment or "").strip()
    if decision not in ("approve", "rework"):
        raise BusinessError("invalid_decision", "Решение должно быть approve или rework")
    if decision == "rework" and not comment:
        raise BusinessError("comment_required", "При возврате на доработку комментарий обязателен",
                            errors=[{"field": "comment", "code": "comment_required",
                                     "message": "Укажите причину возврата"}])
    with transaction.atomic():
        analysis = lock(analysis_id, ON_APPROVAL_STATUSES)
        step = (ApprovalStep.objects.select_for_update()
                .filter(analysis=analysis, iteration=analysis.iteration, status=ApprovalStep.StepStatus.PENDING)
                .first())
        if step is None or (step_id is not None and int(step_id) != step.pk):
            raise ConflictError("step_already_processed", "Шаг уже обработан. Обновите страницу.")
        if not access.is_step_executor(user, step):
            raise PermissionDenied("Вы не являетесь текущим исполнителем шага")

        now = timezone.now()
        profile = getattr(user, "profile", None)
        step.decided_by = user
        step.decided_by_name = full_name(user)
        step.decided_by_position = profile.position if profile else ""
        step.comment = comment
        step.decided_at = now

        if decision == "rework":
            step.status = ApprovalStep.StepStatus.RETURNED
            step.save()
            analysis.steps.filter(iteration=analysis.iteration, status=ApprovalStep.StepStatus.WAITING).update(
                status=ApprovalStep.StepStatus.SKIPPED)
            analysis.returned_from_stage = step.stage
            analysis.current_stage = None
            _transition(analysis, S.REWORK, user=user, request=request, action="returned_for_rework",
                        comment=comment, payload={"step_id": step.pk, "stage": step.stage})
            notify([analysis.author], "ma_returned", f"Маркетинговый анализ {analysis.number} возвращён на доработку",
                   f"{step.decided_by_name}: {comment}", _link(analysis))
            return analysis

        step.status = ApprovalStep.StepStatus.APPROVED
        step.save()
        next_step = (analysis.steps.filter(iteration=analysis.iteration, status=ApprovalStep.StepStatus.WAITING)
                     .order_by("stage", "order").first())
        if next_step is not None:
            next_step.status = ApprovalStep.StepStatus.PENDING
            next_step.activated_at = now
            next_step.save()
            if next_step.stage != step.stage:
                analysis.current_stage = next_step.stage
                _transition(analysis, STAGE_STATUS[Stage(next_step.stage)], user=user, request=request,
                            action="step_approved", comment=comment, payload={"step_id": step.pk})
            else:
                audit(analysis, "step_approved", user=user, request=request, from_status=analysis.status,
                      to_status=analysis.status, comment=comment, payload={"step_id": step.pk})
            _notify_step(analysis, next_step)
            return analysis

        analysis.current_stage = None
        analysis.approved_at = now
        analysis.pdf_status = PdfStatus.PENDING
        _transition(analysis, S.APPROVED, user=user, request=request, action="approved", comment=comment,
                    payload={"step_id": step.pk})
        _publish_to_catalog(analysis)
        recipients = [analysis.author] + ([analysis.initiator_user] if analysis.initiator_user else [])
        notify(recipients, "ma_approved", f"Маркетинговый анализ {analysis.number} утверждён",
               f"Утвердил: {step.decided_by_name}", _link(analysis))

        def _schedule_pdf():
            from .tasks import generate_conclusion_pdf

            try:
                generate_conclusion_pdf.delay(analysis.pk)
            except Exception:
                import logging

                logging.getLogger(__name__).exception("Не удалось поставить генерацию PDF в очередь")

        transaction.on_commit(_schedule_pdf)
    return analysis


def _publish_to_catalog(analysis):
    """Утверждённый анализ попадает в «Каталог цен» как действующее исследование.

    TODO(PO): предыдущие записи каталога по тому же коду АСУ НСИ и ДЗО помечаются недействующими.
    """
    for item in analysis.items.all():
        PriceCatalogEntry.objects.filter(nsi_code=item.nsi_code, dzo_id=analysis.dzo_id, is_active=True).update(
            is_active=False)
        PriceCatalogEntry.objects.create(
            nsi_code=item.nsi_code, enstru_code=item.enstru_code, name=item.name, unit=item.unit,
            dzo_id=analysis.dzo_id, price_wo_vat=item.marketing_price, approved_at=analysis.approved_at,
            source_type="marketing_analysis", source_id=str(analysis.pk), source_number=analysis.number,
        )


def cancel(analysis_id, *, user, comment="", request=None):
    with transaction.atomic():
        analysis = lock(analysis_id, list(EDITABLE_STATUSES))
        if not access.can_edit(user, analysis):
            raise PermissionDenied()
        analysis.cancelled_at = timezone.now()
        analysis.current_stage = None
        _transition(analysis, S.CANCELLED, user=user, request=request, action="cancelled", comment=comment)
    return analysis
