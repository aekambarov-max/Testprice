"""Общие сервисы: журнал аудита, генератор номеров, курсы НБ РК, проверка БИН."""

import logging
from datetime import date
from decimal import Decimal

from django.conf import settings
from django.db import transaction

from .models import AuditLog, CurrencyRate, NumberSequence

logger = logging.getLogger(__name__)


def client_ip(request):
    if request is None:
        return None
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def audit(obj, action, *, user=None, request=None, from_status="", to_status="", comment="", payload=None):
    """Запись в журнал аудита. Вызывается внутри транзакции бизнес-операции."""
    if user is None and request is not None and request.user.is_authenticated:
        user = request.user
    return AuditLog.objects.create(
        user=user,
        ip_address=client_ip(request),
        object_type=obj._meta.label_lower,
        object_id=str(obj.pk),
        action=action,
        from_status=from_status or "",
        to_status=to_status or "",
        comment=comment or "",
        payload=payload or {},
    )


def next_document_number(dzo_code, *, prefix, year=None):
    """Генератор номеров в формате текущих заявок: {prefix}{год}.{код ДЗО}.{NNNN}, например ID2026.EMG.0001."""
    year = year or date.today().year
    with transaction.atomic():
        seq, _ = NumberSequence.objects.select_for_update().get_or_create(prefix=prefix, year=year, dzo_code=dzo_code)
        seq.last_value += 1
        seq.save(update_fields=["last_value"])
    return f"{prefix}{year}.{dzo_code}.{seq.last_value:04d}"


class CurrencyRateMissing(Exception):
    pass


def get_rate(currency, on_date):
    """Курс НБ РК на дату (или ближайшую предыдущую дату публикации)."""
    currency = (currency or "").upper()
    if currency == settings.BASE_CURRENCY:
        return Decimal("1")
    rate = CurrencyRate.objects.filter(currency=currency, date__lte=on_date).order_by("-date").first()
    if rate is None:
        raise CurrencyRateMissing(f"Нет курса НБ РК для {currency} на {on_date:%d.%m.%Y}")
    return rate.rate


_BIN_WEIGHTS_1 = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)
_BIN_WEIGHTS_2 = (3, 4, 5, 6, 7, 8, 9, 10, 11, 1, 2)


def is_valid_bin(value):
    """Проверка контрольного разряда БИН/ИИН (12 цифр)."""
    if not value or len(value) != 12 or not value.isdigit():
        return False
    digits = [int(c) for c in value]
    control = sum(d * w for d, w in zip(digits, _BIN_WEIGHTS_1)) % 11
    if control == 10:
        control = sum(d * w for d, w in zip(digits, _BIN_WEIGHTS_2)) % 11
        if control == 10:
            return False
    return control == digits[11]


def gbd_ul_lookup(bin_value):
    """Поиск юрлица в ГБД ЮЛ.

    TODO(PO): интеграция с ГБД ЮЛ через SAP PI/PO отсутствует в MVP — ищем только в локальном пуле поставщиков.
    """
    from apps.suppliers.models import Supplier

    supplier = Supplier.objects.filter(bin=bin_value).first()
    return {"bin": supplier.bin, "name": supplier.name} if supplier else None
