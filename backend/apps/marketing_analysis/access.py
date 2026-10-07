"""Права доступа подмодуля (раздел 4 ТЗ). Все проверки — на backend: на уровне queryset и на уровне действия."""

from django.db.models import Q

from apps.core import roles
from apps.core.access import marketer_dzo_ids

from .models import EDITABLE_STATUSES, ON_APPROVAL_STATUSES, ApprovalStep, MarketingAnalysis, Status

GLOBAL_VIEW_ROLES = (roles.ADMIN, roles.DB_SPECIALIST, roles.DB_DIRECTOR)


def visible_analyses(user):
    """Анализы, которые пользователь вправе видеть. Чужой анализ по ID → 404."""
    qs = MarketingAnalysis.objects.all()
    user_roles = roles.user_roles(user)
    if user_roles & set(GLOBAL_VIEW_ROLES):
        return qs
    condition = Q(steps__assignee_user=user) | Q(approvers__user=user)
    if roles.MARKETER in user_roles:
        condition |= Q(dzo_id__in=marketer_dzo_ids(user))
    return qs.filter(condition).distinct()


def is_marketer_for(user, analysis):
    return roles.has_role(user, roles.MARKETER) and analysis.dzo_id in marketer_dzo_ids(user)


def can_edit(user, analysis):
    return analysis.status in EDITABLE_STATUSES and is_marketer_for(user, analysis)


def current_step(analysis):
    if analysis.status not in ON_APPROVAL_STATUSES:
        return None
    return (
        analysis.steps.filter(iteration=analysis.iteration, status=ApprovalStep.StepStatus.PENDING)
        .select_related("assignee_user")
        .first()
    )


def is_step_executor(user, step):
    """Текущий исполнитель шага. TODO(PO): замещение (ИО) для Директора и специалистов ДБ КМГ — механизма нет."""
    if step is None:
        return False
    if step.assignee_user_id:
        return step.assignee_user_id == user.pk
    return bool(step.assignee_role) and roles.has_role(user, step.assignee_role)


def available_actions(user, analysis, step=None):
    actions = []
    if can_edit(user, analysis):
        actions += ["edit", "manage_items", "request_kp", "upload_offer", "calculate", "set_approvers"]
        if analysis.status == Status.DRAFT:
            actions += ["start_collecting", "delete"]
        if analysis.status in (Status.COLLECTING_KP, Status.REWORK):
            actions.append("submit")
        actions.append("cancel")
    if analysis.status in ON_APPROVAL_STATUSES:
        step = step if step is not None else current_step(analysis)
        if is_step_executor(user, step):
            actions += ["approve", "rework"]
    if analysis.status == Status.APPROVED:
        actions.append("download_pdf")
        if roles.is_admin(user) and analysis.pdf_status == "failed":
            actions.append("regenerate_pdf")
    return actions
