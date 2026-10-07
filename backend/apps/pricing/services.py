"""Сервис расчёта маркетинговой цены и аналитики. Расчёт выполняется только на backend."""

from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings
from django.db.models import Avg, Count

from .models import PriceCatalogEntry

CENT = Decimal("0.01")


def money(value):
    return Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


def to_kzt_without_vat(price, rate, vat_included):
    value = Decimal(price) * Decimal(rate)
    if vat_included:
        value = value / (Decimal(1) + Decimal(settings.VAT_RATE_PERCENT) / Decimal(100))
    return money(value)


def calculate_marketing_price(prices_kzt_wo_vat, method=None):
    """Маркетинговая цена за единицу без НДС по ценам КП (уже приведённым к KZT без НДС)."""
    method = method or settings.MA_PRICE_CALC_METHOD
    values = [Decimal(p) for p in prices_kzt_wo_vat]
    if not values:
        return None
    if method == "min":
        return money(min(values))
    if method == "average":
        return money(sum(values) / len(values))
    raise ValueError(f"Неизвестный метод расчёта: {method}")


def price_history(nsi_code, *, exclude_source=None, limit=10):
    qs = PriceCatalogEntry.objects.filter(nsi_code=nsi_code).select_related("dzo")
    if exclude_source:
        qs = qs.exclude(source_type=exclude_source[0], source_id=str(exclude_source[1]))
    return [
        {
            "dzo": e.dzo.name_ru,
            "dzo_code": e.dzo.code,
            "price_wo_vat": e.price_wo_vat,
            "approved_at": e.approved_at,
            "source_number": e.source_number,
            "is_active": e.is_active,
        }
        for e in qs[:limit]
    ]


def kmg_average(nsi_code, *, exclude_source=None):
    """Средняя действующая цена по группе КМГ (все ДЗО) по коду АСУ НСИ."""
    qs = PriceCatalogEntry.objects.filter(nsi_code=nsi_code, is_active=True)
    if exclude_source:
        qs = qs.exclude(source_type=exclude_source[0], source_id=str(exclude_source[1]))
    agg = qs.aggregate(avg=Avg("price_wo_vat"), n=Count("id"))
    return (money(agg["avg"]) if agg["avg"] is not None else None), agg["n"]


def deviation_percent(price, reference):
    if price is None or not reference:
        return None
    return money((Decimal(price) - Decimal(reference)) / Decimal(reference) * 100)
