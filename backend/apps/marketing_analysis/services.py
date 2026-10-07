"""Операции с данными анализа (позиции, КП, расчёт, согласующие). Доступны только в редактируемых статусах."""

import json
import os
from datetime import date
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Max
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from apps.core.exceptions import BusinessError, ConflictError
from apps.core.models import UserProfile
from apps.core.services import CurrencyRateMissing, audit, get_rate, is_valid_bin, next_document_number
from apps.nsi.models import NsiProduct
from apps.pricing import services as pricing
from apps.suppliers.models import KpRequest, Supplier
from apps.suppliers.services import register_response_handler, send_kp_requests

from . import access, workflow
from .models import (
    EDITABLE_STATUSES,
    AnalysisApprover,
    CommercialOffer,
    CommercialOfferPrice,
    ItemAttachment,
    MarketingAnalysis,
    MarketingAnalysisItem,
    Status,
)

SOURCE_TYPE = "marketing_analysis"


def _editable(analysis_id, user):
    """Блокирует анализ и проверяет право редактирования."""
    analysis = workflow.lock(analysis_id, list(EDITABLE_STATUSES))
    if not access.can_edit(user, analysis):
        raise PermissionDenied()
    return analysis


def _auto_start_collecting(analysis, user, request):
    if analysis.status == Status.DRAFT:
        workflow._transition(analysis, Status.COLLECTING_KP, user=user, request=request, action="collecting_started")


def _invalidate_prices(analysis, item_ids=None):
    qs = analysis.items.all()
    if item_ids is not None:
        qs = qs.filter(pk__in=item_ids)
    qs.update(marketing_price=None, total_wo_vat=None, calc_method="")
    MarketingAnalysis.objects.filter(pk=analysis.pk).update(total_wo_vat=None)
    analysis.total_wo_vat = None


def _decimal(value, field, *, positive=True):
    try:
        result = Decimal(str(value).replace(",", ".").replace(" ", ""))
    except (InvalidOperation, TypeError):
        raise BusinessError("invalid_number", f"Некорректное число в поле «{field}»",
                            errors=[{"field": field, "code": "invalid_number", "message": "Некорректное число"}])
    if positive and result <= 0:
        raise BusinessError("must_be_positive", f"Значение «{field}» должно быть больше нуля",
                            errors=[{"field": field, "code": "must_be_positive", "message": "Должно быть больше нуля"}])
    return result


def _check_file(upload, allowed=None):
    if upload is None:
        raise BusinessError("file_required", "Приложите файл", errors=[{"field": "file", "code": "file_required",
                                                                        "message": "Приложите файл"}])
    ext = os.path.splitext(upload.name)[1].lower().lstrip(".")
    allowed = allowed or settings.MA_ALLOWED_OFFER_EXTENSIONS
    if ext not in allowed:
        raise BusinessError("file_type", f"Недопустимый тип файла. Разрешены: {', '.join(allowed).upper()}",
                            errors=[{"field": "file", "code": "file_type", "message": "Недопустимый тип файла"}])
    if upload.size > settings.MA_MAX_UPLOAD_MB * 1024 * 1024:
        raise BusinessError("file_size", f"Файл больше {settings.MA_MAX_UPLOAD_MB} МБ",
                            errors=[{"field": "file", "code": "file_size", "message": "Слишком большой файл"}])


# --- Анализ ---------------------------------------------------------------------------------------------------

def _apply_initiator(analysis, data):
    if "initiator_user" in data:
        user_id = data.get("initiator_user")
        analysis.initiator_user = get_user_model().objects.filter(pk=user_id, is_active=True).first() if user_id else None
        if user_id and analysis.initiator_user is None:
            raise BusinessError("initiator_not_found", "Сотрудник не найден")
        if analysis.initiator_user:
            analysis.initiator_full_name = ""
            analysis.initiator_position = ""
            analysis.initiator_department = ""
    for field in ("initiator_full_name", "initiator_position", "initiator_department"):
        if field in data and not analysis.initiator_user:
            setattr(analysis, field, (data.get(field) or "").strip())
    if "price_justification" in data:
        analysis.price_justification = data.get("price_justification") or ""


def create_analysis(*, user, data, request=None):
    from apps.core.access import marketer_dzo_ids
    from apps.core.models import Dzo
    from apps.core.roles import MARKETER, has_role

    if not has_role(user, MARKETER):
        raise PermissionDenied("Создавать маркетинговый анализ может только маркетолог")
    dzo_id = data.get("dzo")
    if not dzo_id:
        profile = UserProfile.objects.filter(user=user).first()
        dzo_id = profile.dzo_id if profile else None
    if not dzo_id:
        raise BusinessError("dzo_required", "Укажите ДЗО", errors=[{"field": "dzo", "code": "dzo_required",
                                                                    "message": "Укажите ДЗО"}])
    if int(dzo_id) not in marketer_dzo_ids(user):
        raise PermissionDenied("Нет доступа к выбранному ДЗО")
    dzo = Dzo.objects.get(pk=dzo_id)
    with transaction.atomic():
        analysis = MarketingAnalysis(dzo=dzo, author=user,
                                     number=next_document_number(dzo.code, prefix=settings.MA_NUMBER_PREFIX))
        _apply_initiator(analysis, data)
        analysis.save()
        audit(analysis, "created", user=user, request=request, to_status=analysis.status)
    return analysis


def update_analysis(analysis_id, *, user, data, request=None):
    with transaction.atomic():
        analysis = _editable(analysis_id, user)
        if "dzo" in data and data["dzo"] and int(data["dzo"]) != analysis.dzo_id:
            raise BusinessError("dzo_immutable", "ДЗО нельзя изменить после создания анализа (номер уже присвоен)")
        _apply_initiator(analysis, data)
        analysis.save()
        audit(analysis, "updated", user=user, request=request, payload={"fields": sorted(data.keys())})
    return analysis


def delete_draft(analysis_id, *, user, request=None):
    with transaction.atomic():
        analysis = workflow.lock(analysis_id, [Status.DRAFT])
        if not access.can_edit(user, analysis):
            raise PermissionDenied()
        audit(analysis, "deleted", user=user, request=request, from_status=analysis.status)
        analysis.delete()


# --- Позиции ---------------------------------------------------------------------------------------------------

def add_item(analysis_id, *, user, data, request=None):
    product = NsiProduct.objects.filter(pk=data.get("nsi_product"), is_active=True).first()
    if product is None:
        raise BusinessError("nsi_product_required", "Выберите товар из справочника АСУ НСИ",
                            errors=[{"field": "nsi_product", "code": "required", "message": "Выберите товар"}])
    quantity = _decimal(data.get("quantity"), "quantity")
    with transaction.atomic():
        analysis = _editable(analysis_id, user)
        line_no = (analysis.items.aggregate(m=Max("line_no"))["m"] or 0) + 1
        item = MarketingAnalysisItem.objects.create(
            analysis=analysis, line_no=line_no, nsi_product=product,
            nsi_code=product.nsi_code, enstru_code=product.enstru_code, name=product.name,
            characteristics=product.short_description, unit=product.unit, quantity=quantity,
            delivery_place=(data.get("delivery_place") or "").strip(),
            delivery_term=(data.get("delivery_term") or "").strip(),
        )
        _recalculate_total(analysis)
        audit(analysis, "item_added", user=user, request=request,
              payload={"item_id": item.pk, "nsi_code": item.nsi_code, "quantity": str(quantity)})
    return item


def update_item(analysis_id, item_id, *, user, data, request=None):
    with transaction.atomic():
        analysis = _editable(analysis_id, user)
        item = analysis.items.get(pk=item_id)
        changes = {}
        if "quantity" in data:
            item.quantity = _decimal(data["quantity"], "quantity")
            changes["quantity"] = str(item.quantity)
            if item.marketing_price is not None:
                item.total_wo_vat = pricing.money(item.marketing_price * item.quantity)
        for field in ("delivery_place", "delivery_term", "price_justification"):
            if field in data:
                setattr(item, field, (data.get(field) or "").strip())
                changes[field] = getattr(item, field)
        item.save()
        _recalculate_total(analysis)
        audit(analysis, "item_updated", user=user, request=request, payload={"item_id": item.pk, **changes})
    return item


def delete_item(analysis_id, item_id, *, user, request=None):
    with transaction.atomic():
        analysis = _editable(analysis_id, user)
        item = analysis.items.get(pk=item_id)
        audit(analysis, "item_deleted", user=user, request=request,
              payload={"item_id": item.pk, "nsi_code": item.nsi_code})
        item.delete()
        _recalculate_total(analysis)


def add_attachment(analysis_id, item_id, *, user, upload, request=None):
    _check_file(upload)
    with transaction.atomic():
        analysis = _editable(analysis_id, user)
        item = analysis.items.get(pk=item_id)
        att = ItemAttachment.objects.create(item=item, file=upload, original_name=upload.name, uploaded_by=user)
        audit(analysis, "attachment_added", user=user, request=request,
              payload={"item_id": item.pk, "attachment_id": att.pk, "name": upload.name})
    return att


def delete_attachment(analysis_id, item_id, attachment_id, *, user, request=None):
    with transaction.atomic():
        analysis = _editable(analysis_id, user)
        att = ItemAttachment.objects.get(pk=attachment_id, item_id=item_id, item__analysis=analysis)
        audit(analysis, "attachment_deleted", user=user, request=request,
              payload={"item_id": item_id, "attachment_id": att.pk, "name": att.original_name})
        att.file.delete(save=False)
        att.delete()


# --- Коммерческие предложения ----------------------------------------------------------------------------------

def _parse_prices(raw):
    if isinstance(raw, str):
        try:
            raw = json.loads(raw or "{}")
        except ValueError:
            raise BusinessError("invalid_prices", "Некорректный формат цен")
    if isinstance(raw, list):
        raw = {str(p.get("item")): p.get("price") for p in raw}
    return {str(k): v for k, v in (raw or {}).items() if v not in (None, "")}


def _create_offer(analysis, *, user, data, upload, source, kp_request=None, supplier=None):
    _check_file(upload)
    supplier_bin = (data.get("supplier_bin") or (supplier.bin if supplier else "")).strip()
    if not is_valid_bin(supplier_bin):
        raise BusinessError("invalid_bin", "Некорректный БИН поставщика (12 цифр, контрольный разряд)",
                            errors=[{"field": "supplier_bin", "code": "invalid_bin", "message": "Некорректный БИН"}])
    supplier = supplier or Supplier.objects.filter(bin=supplier_bin).first()
    supplier_name = (data.get("supplier_name") or (supplier.name if supplier else "")).strip()
    if not supplier_name:
        raise BusinessError("supplier_name_required", "Укажите наименование поставщика",
                            errors=[{"field": "supplier_name", "code": "required", "message": "Укажите поставщика"}])
    try:
        offer_date = date.fromisoformat(str(data.get("offer_date")))
    except ValueError:
        raise BusinessError("offer_date_required", "Укажите дату КП",
                            errors=[{"field": "offer_date", "code": "required", "message": "Укажите дату КП"}])
    if offer_date > date.today():
        raise BusinessError("offer_date_future", "Дата КП не может быть в будущем",
                            errors=[{"field": "offer_date", "code": "future", "message": "Дата в будущем"}])
    currency = (data.get("currency") or settings.BASE_CURRENCY).upper()
    try:
        rate = get_rate(currency, offer_date)
    except CurrencyRateMissing as exc:
        raise BusinessError("rate_missing", str(exc), errors=[{"field": "currency", "code": "rate_missing",
                                                               "message": str(exc)}])
    vat_included = str(data.get("vat_included", "false")).lower() in ("1", "true", "on", "yes")
    prices = _parse_prices(data.get("prices"))
    items = {str(i.pk): i for i in analysis.items.all()}
    unknown = set(prices) - set(items)
    if unknown:
        raise BusinessError("unknown_items", "Цены указаны для позиций, которых нет в анализе")
    if not prices:
        raise BusinessError("prices_required", "Укажите цену хотя бы по одной позиции",
                            errors=[{"field": "prices", "code": "required", "message": "Укажите цены"}])

    offer = CommercialOffer.objects.create(
        analysis=analysis, supplier=supplier, supplier_name=supplier_name, supplier_bin=supplier_bin,
        offer_date=offer_date, currency=currency, exchange_rate=rate, vat_included=vat_included,
        file=upload, original_name=upload.name, source=source, kp_request=kp_request, created_by=user,
    )
    for item_id, value in prices.items():
        price = _decimal(value, f"prices.{item_id}")
        CommercialOfferPrice.objects.create(
            offer=offer, item=items[item_id], price=price,
            price_kzt_wo_vat=pricing.to_kzt_without_vat(price, rate, vat_included),
        )
    _invalidate_prices(analysis, item_ids=[int(i) for i in prices])
    return offer


def add_offer(analysis_id, *, user, data, upload, request=None):
    with transaction.atomic():
        analysis = _editable(analysis_id, user)
        offer = _create_offer(analysis, user=user, data=data, upload=upload, source=CommercialOffer.Source.MANUAL)
        _auto_start_collecting(analysis, user, request)
        audit(analysis, "offer_uploaded", user=user, request=request,
              payload={"offer_id": offer.pk, "supplier_bin": offer.supplier_bin, "file": offer.original_name})
    return offer


def delete_offer(analysis_id, offer_id, *, user, request=None):
    with transaction.atomic():
        analysis = _editable(analysis_id, user)
        offer = analysis.offers.get(pk=offer_id)
        item_ids = list(offer.prices.values_list("item_id", flat=True))
        audit(analysis, "offer_deleted", user=user, request=request,
              payload={"offer_id": offer.pk, "supplier_bin": offer.supplier_bin, "file": offer.original_name})
        offer.file.delete(save=False)
        offer.delete()
        _invalidate_prices(analysis, item_ids=item_ids)


def handle_supplier_response(request, kp_request):
    """КП, поданное поставщиком по ссылке из запроса, автоматически подтягивается в анализ."""
    try:
        with transaction.atomic():
            analysis = workflow.lock(int(kp_request.source_id), list(EDITABLE_STATUSES))
            offer = _create_offer(analysis, user=None, data=request.data, upload=request.FILES.get("file"),
                                  source=CommercialOffer.Source.SYSTEM, kp_request=kp_request,
                                  supplier=kp_request.supplier)
            KpRequest.objects.filter(pk=kp_request.pk).update(status=KpRequest.Status.ANSWERED,
                                                              answered_at=offer.created_at)
            audit(analysis, "offer_received", request=request,
                  payload={"offer_id": offer.pk, "kp_request_id": kp_request.pk, "supplier_bin": offer.supplier_bin})
    except ConflictError:
        return Response({"code": "closed", "detail": "Приём КП по этому запросу завершён"}, status=409)
    return Response({"id": offer.pk}, status=201)


register_response_handler(SOURCE_TYPE, handle_supplier_response)


def request_kp(analysis_id, *, user, supplier_ids, message="", request=None):
    suppliers = list(Supplier.objects.filter(pk__in=supplier_ids or [], is_active=True))
    if not suppliers:
        raise BusinessError("suppliers_required", "Выберите поставщиков из пула")
    with transaction.atomic():
        analysis = _editable(analysis_id, user)
        items = [{"nsi_code": i.nsi_code, "name": i.name, "characteristics": i.characteristics, "unit": i.unit,
                  "quantity": str(i.quantity), "item_id": i.pk, "delivery_place": i.delivery_place,
                  "delivery_term": i.delivery_term} for i in analysis.items.all()]
        if not items:
            raise BusinessError("items_required", "Сначала добавьте позиции")
        sent = send_kp_requests(source_type=SOURCE_TYPE, source_id=analysis.pk, suppliers=suppliers, items=items,
                                sender=user, subject=f"Запрос коммерческого предложения {analysis.number}",
                                message=message)
        _auto_start_collecting(analysis, user, request)
        audit(analysis, "kp_requested", user=user, request=request,
              payload={"supplier_ids": [s.pk for s in suppliers]})
    return sent


# --- Расчёт и аналитика -----------------------------------------------------------------------------------------

def _recalculate_total(analysis):
    totals = list(analysis.items.values_list("total_wo_vat", flat=True))
    total = sum(totals) if totals and all(t is not None for t in totals) else None
    MarketingAnalysis.objects.filter(pk=analysis.pk).update(total_wo_vat=total)
    analysis.total_wo_vat = total


def calculate(analysis_id, *, user, request=None):
    """Расчёт маркетинговой цены сервисом pricing по всем позициям."""
    with transaction.atomic():
        analysis = _editable(analysis_id, user)
        method = settings.MA_PRICE_CALC_METHOD
        result = []
        for item in analysis.items.prefetch_related("offer_prices"):
            values = [p.price_kzt_wo_vat for p in item.offer_prices.all()]
            item.marketing_price = pricing.calculate_marketing_price(values, method)
            item.total_wo_vat = pricing.money(item.marketing_price * item.quantity) if item.marketing_price else None
            item.calc_method = method if item.marketing_price is not None else ""
            item.save(update_fields=["marketing_price", "total_wo_vat", "calc_method"])
            result.append({"item_id": item.pk, "marketing_price": str(item.marketing_price),
                           "offers": len(values)})
        _recalculate_total(analysis)
        audit(analysis, "calculated", user=user, request=request, payload={"method": method, "items": result})
    return analysis


def analytics(analysis):
    exclude = (SOURCE_TYPE, analysis.pk)
    items = []
    for item in analysis.items.prefetch_related("offer_prices__offer"):
        offers = [
            {"offer_id": p.offer_id, "supplier_name": p.offer.supplier_name, "supplier_bin": p.offer.supplier_bin,
             "price": p.price, "currency": p.offer.currency, "vat_included": p.offer.vat_included,
             "price_kzt_wo_vat": p.price_kzt_wo_vat}
            for p in item.offer_prices.all()
        ]
        values = [o["price_kzt_wo_vat"] for o in offers]
        kmg_avg, kmg_count = pricing.kmg_average(item.nsi_code, exclude_source=exclude)
        deviation = pricing.deviation_percent(item.marketing_price, kmg_avg)
        items.append({
            "item_id": item.pk, "line_no": item.line_no, "nsi_code": item.nsi_code, "name": item.name,
            "unit": item.unit, "quantity": item.quantity, "offers": offers,
            "min": min(values) if values else None, "max": max(values) if values else None,
            "average": pricing.money(sum(values) / len(values)) if values else None,
            "marketing_price": item.marketing_price, "total_wo_vat": item.total_wo_vat,
            "kmg_average": kmg_avg, "kmg_count": kmg_count, "deviation_from_kmg_percent": deviation,
            # TODO(PO): вопрос 6 — нужна ли отправка Ответственному за маркетинг цен КМГ при превышении порога.
            "deviation_exceeds_threshold": (
                deviation is not None and abs(deviation) > settings.MA_KMG_DEVIATION_THRESHOLD_PERCENT),
            "history": pricing.price_history(item.nsi_code, exclude_source=exclude),
        })
    participants = analysis.offers.values("supplier_bin").distinct().count()
    return {"calc_method": settings.MA_PRICE_CALC_METHOD, "vat_rate_percent": settings.VAT_RATE_PERCENT,
            "participants": participants, "total_wo_vat": analysis.total_wo_vat, "items": items}


# --- Согласующие этапа 1 -----------------------------------------------------------------------------------------

def set_approvers(analysis_id, *, user, user_ids, request=None):
    user_ids = [int(u) for u in (user_ids or [])]
    if len(set(user_ids)) != len(user_ids):
        raise BusinessError("duplicate_approvers", "Согласующий указан дважды")
    with transaction.atomic():
        analysis = _editable(analysis_id, user)
        users = get_user_model().objects.filter(pk__in=user_ids, is_active=True).select_related("profile")
        by_id = {u.pk: u for u in users}
        errors = []
        for uid in user_ids:
            approver = by_id.get(uid)
            if approver is None:
                errors.append({"user_id": uid, "code": "not_found", "message": "Пользователь не найден"})
                continue
            if approver.pk == analysis.author_id and not settings.MA_ALLOW_AUTHOR_AS_APPROVER:
                errors.append({"user_id": uid, "code": "author", "message": "Автор не может быть согласующим"})
            profile = getattr(approver, "profile", None)
            if settings.MA_DZO_APPROVERS_SAME_DZO_ONLY and (profile is None or profile.dzo_id != analysis.dzo_id):
                errors.append({"user_id": uid, "code": "other_dzo",
                               "message": "Согласующий должен быть сотрудником ДЗО анализа"})
        if errors:
            raise BusinessError("invalid_approvers", "Некорректный список согласующих", errors=errors)
        analysis.approvers.all().delete()
        AnalysisApprover.objects.bulk_create(
            [AnalysisApprover(analysis=analysis, user=by_id[uid], order=i) for i, uid in enumerate(user_ids, 1)])
        audit(analysis, "approvers_set", user=user, request=request, payload={"user_ids": user_ids})
    return analysis
