import json
from datetime import date, timedelta
from decimal import Decimal

import pytest

from apps.core.services import is_valid_bin, next_document_number
from apps.marketing_analysis.models import CommercialOffer, MarketingAnalysisItem
from apps.pricing.services import calculate_marketing_price, to_kzt_without_vat
from apps.suppliers.models import KpRequest
from tests.conftest import VALID_BINS, client_for, create_analysis, pdf_file


def test_price_calculation_methods(settings):
    settings.VAT_RATE_PERCENT = 16
    assert calculate_marketing_price([Decimal("100"), Decimal("200")], "average") == Decimal("150.00")
    assert calculate_marketing_price([Decimal("100"), Decimal("200")], "min") == Decimal("100.00")
    assert calculate_marketing_price([], "average") is None
    assert to_kzt_without_vat(Decimal("116"), Decimal("1"), True) == Decimal("100.00")
    assert to_kzt_without_vat(Decimal("10"), Decimal("500"), False) == Decimal("5000.00")


def test_bin_checksum():
    for value in VALID_BINS:
        assert is_valid_bin(value)
    assert not is_valid_bin("050140000012")
    assert not is_valid_bin("12345")
    assert not is_valid_bin("abcdefghijkl")


@pytest.mark.django_db
def test_number_generator_sequence():
    assert next_document_number("EMG", prefix="ID", year=2026) == "ID2026.EMG.0001"
    assert next_document_number("EMG", prefix="ID", year=2026) == "ID2026.EMG.0002"
    assert next_document_number("MMG", prefix="ID", year=2026) == "ID2026.MMG.0001"


@pytest.mark.django_db
def test_item_snapshot_survives_nsi_change(world):
    w = world
    aid, item_ids = create_analysis(w)
    w.product1.name = "Новое наименование"
    w.product1.save()
    assert MarketingAnalysisItem.objects.get(pk=item_ids[0]).name == "Труба стальная 89х6"


@pytest.mark.django_db
def test_calculation_and_analytics(world):
    w = world
    aid, item_ids = create_analysis(w, items=(("product1", "10"),))
    item = MarketingAnalysisItem.objects.get(pk=item_ids[0])
    assert item.marketing_price == Decimal("1100.00")  # среднее 1000 и 1200
    assert item.total_wo_vat == Decimal("11000.00")
    r = client_for(w.marketer).get(f"/api/marketing-analyses/{aid}/analytics/")
    data = r.data["items"][0]
    assert data["min"] == Decimal("1000.00") and data["max"] == Decimal("1200.00")
    assert r.data["participants"] == 2
    # изменение количества пересчитывает сумму без повторного расчёта цены
    r = client_for(w.marketer).patch(f"/api/marketing-analyses/{aid}/items/{item.pk}/", {"quantity": "3"},
                                     format="json")
    assert r.data["total_wo_vat"] == "3300.00"


@pytest.mark.django_db
def test_offer_in_foreign_currency_with_vat(world):
    w = world
    aid, item_ids = create_analysis(w, offers=False, calculate=False)
    r = client_for(w.marketer).post(f"/api/marketing-analyses/{aid}/offers/", {
        "file": pdf_file(), "supplier_bin": VALID_BINS[0], "offer_date": date.today().isoformat(),
        "currency": "USD", "vat_included": "true", "prices": json.dumps({str(item_ids[0]): "11.6"})},
        format="multipart")
    assert r.status_code == 201, r.data
    assert r.data["exchange_rate"] == "500.0000"
    assert r.data["prices"][0]["price_kzt_wo_vat"] == "5000.00"  # 11.6 * 500 / 1.16


@pytest.mark.django_db
@pytest.mark.parametrize("override,code", [
    ({"supplier_bin": "123456789012"}, "invalid_bin"),
    ({"currency": "GBP"}, "rate_missing"),
    ({"offer_date": (date.today() + timedelta(days=2)).isoformat()}, "offer_date_future"),
    ({"prices": "{}"}, "prices_required"),
    ({"file": "exe"}, "file_type"),
])
def test_offer_validation(world, override, code):
    w = world
    aid, item_ids = create_analysis(w, offers=False, calculate=False)
    from django.core.files.uploadedfile import SimpleUploadedFile

    data = {"file": pdf_file(), "supplier_bin": VALID_BINS[0], "offer_date": date.today().isoformat(),
            "currency": "KZT", "prices": json.dumps({str(item_ids[0]): "100"}), **override}
    if data["file"] == "exe":
        data["file"] = SimpleUploadedFile("virus.exe", b"MZ")
    r = client_for(w.marketer).post(f"/api/marketing-analyses/{aid}/offers/", data, format="multipart")
    assert r.status_code == 400 and r.data["code"] == code


@pytest.mark.django_db
def test_request_kp_and_supplier_response_is_pulled_in(world):
    w = world
    aid, item_ids = create_analysis(w, offers=False, calculate=False)
    r = client_for(w.marketer).post(f"/api/marketing-analyses/{aid}/request-kp/",
                                    {"suppliers": [s.pk for s in w.suppliers[:2]], "message": "Срок 5 дней"},
                                    format="json")
    assert r.status_code == 200 and r.data["sent"] == 2
    from django.core import mail

    assert len(mail.outbox) == 2 and "/kp/" in mail.outbox[0].body
    req = KpRequest.objects.filter(source_id=str(aid)).first()

    from rest_framework.test import APIClient

    anon = APIClient()
    assert anon.get(f"/api/kp-responses/{req.token}/").data["items"][0]["nsi_code"] == "1010101001"
    r = anon.post(f"/api/kp-responses/{req.token}/", {
        "file": pdf_file(), "offer_date": date.today().isoformat(), "currency": "KZT",
        "prices": json.dumps({str(item_ids[0]): "950"})}, format="multipart")
    assert r.status_code == 201, r.data
    offer = CommercialOffer.objects.get(pk=r.data["id"])
    assert offer.source == "system" and offer.supplier == req.supplier and offer.analysis_id == aid
    req.refresh_from_db()
    assert req.status == "answered"


@pytest.mark.django_db
def test_supplier_response_rejected_after_submit(world):
    w = world
    aid, item_ids = create_analysis(w)
    client_for(w.marketer).post(f"/api/marketing-analyses/{aid}/request-kp/", {"suppliers": [w.suppliers[2].pk]},
                                format="json")
    client_for(w.marketer).post(f"/api/marketing-analyses/{aid}/submit/")
    req = KpRequest.objects.get(source_id=str(aid))
    from rest_framework.test import APIClient

    r = APIClient().post(f"/api/kp-responses/{req.token}/", {
        "file": pdf_file(), "offer_date": date.today().isoformat(), "currency": "KZT",
        "prices": json.dumps({str(item_ids[0]): "950"})}, format="multipart")
    assert r.status_code == 409


@pytest.mark.django_db
def test_initiator_from_directory_or_manual(world):
    w = world
    c = client_for(w.marketer)
    r = c.post("/api/marketing-analyses/", {"dzo": w.emg.pk, "initiator_user": w.approver1.pk}, format="json")
    assert r.data["initiator"] == "Approver1 Тест"
    aid = r.data["id"]
    r = c.patch(f"/api/marketing-analyses/{aid}/", {"initiator_user": None, "initiator_full_name": "Петров П.П.",
                                                    "initiator_position": "Механик"}, format="json")
    assert r.data["initiator"] == "Петров П.П." and r.data["initiator_position"] == "Механик"
    r = c.patch(f"/api/marketing-analyses/{aid}/", {"dzo": w.mmg.pk}, format="json")
    assert r.status_code == 400 and r.data["code"] == "dzo_immutable"


@pytest.mark.django_db
def test_lookup_endpoints(world):
    c = client_for(world.marketer)
    assert c.get("/api/nsi/products/", {"q": "1010"}).data[0]["unit"] == "м"
    assert c.get("/api/nsi/products/", {"q": "Насос"}).data[0]["nsi_code"] == "2020202001"
    assert {u["username"] for u in c.get("/api/users/search/", {"q": "approver"}).data} == {
        "approver1", "approver2", "approvermmg"}
    assert len(c.get("/api/suppliers/").data) == 3
    me = c.get("/api/auth/me/").data
    assert me["user"]["roles"] == ["marketer"] and me["user"]["allowed_dzos"][0]["code"] == "EMG"
