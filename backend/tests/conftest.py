from datetime import date, timedelta

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from apps.core import roles
from apps.core.models import CurrencyRate, Dzo, UserProfile
from apps.nsi.models import NsiProduct
from apps.suppliers.models import Supplier

VALID_BINS = ["050140000011", "060240000027", "070340000032"]


@pytest.fixture(autouse=True)
def _on_commit_immediately(request, monkeypatch):
    """В тестах с откатываемой транзакцией on_commit-колбэки (Celery-задачи) выполняем сразу."""
    marker = request.node.get_closest_marker("django_db")
    if marker and marker.kwargs.get("transaction"):
        return
    from django.db import transaction

    monkeypatch.setattr(transaction, "on_commit", lambda func, using=None, robust=False: func())


@pytest.fixture(autouse=True)
def _media(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / "media"
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.MA_ENABLED = True
    settings.MA_MIN_KP_COUNT = 1
    settings.MA_RESTART_ROUTE_FROM_BEGINNING = True
    settings.MA_ALLOW_SKIP_DZO_STAGE = False
    settings.MA_DZO_APPROVERS_SAME_DZO_ONLY = True
    settings.MA_PRICE_CALC_METHOD = "average"
    settings.VAT_RATE_PERCENT = 16


class World:
    pass


def make_user(username, dzo, role_codes=(), position="Специалист"):
    user = get_user_model().objects.create_user(username, f"{username}@test.local", "pass",
                                                last_name=username.capitalize(), first_name="Тест")
    UserProfile.objects.create(user=user, dzo=dzo, position=position)
    for role in role_codes:
        user.groups.add(Group.objects.get(name=role))
    return user


@pytest.fixture
def world(db):
    w = World()
    w.emg = Dzo.objects.create(code="EMG", name_ru="АО «Эмбамунайгаз»")
    w.mmg = Dzo.objects.create(code="MMG", name_ru="АО «Мангистаумунайгаз»")
    w.kmg = Dzo.objects.create(code="KMG", name_ru="АО НК «КазМунайГаз»")
    w.marketer = make_user("marketer", w.emg, [roles.MARKETER])
    w.marketer2 = make_user("marketer2", w.emg, [roles.MARKETER])
    w.marketer_mmg = make_user("marketermmg", w.mmg, [roles.MARKETER])
    w.approver1 = make_user("approver1", w.emg, position="Начальник отдела МТО")
    w.approver2 = make_user("approver2", w.emg, position="Главный экономист")
    w.outsider = make_user("outsider", w.emg)
    w.approver_mmg = make_user("approvermmg", w.mmg)
    w.db_spec = make_user("dbspec", w.kmg, [roles.DB_SPECIALIST], position="Главный специалист ДБ")
    w.db_dir = make_user("dbdir", w.kmg, [roles.DB_DIRECTOR], position="Директор ДБ")
    w.admin = make_user("admin", w.kmg, [roles.ADMIN])
    w.product1 = NsiProduct.objects.create(nsi_code="1010101001", enstru_code="222011.100.000001",
                                           name="Труба стальная 89х6", short_description="ГОСТ 8732-78", unit="м")
    w.product2 = NsiProduct.objects.create(nsi_code="2020202001", enstru_code="281314.300.000010",
                                           name="Насос НН2Б-44", short_description="ход 3 м", unit="шт")
    w.suppliers = [Supplier.objects.create(bin=b, name=f"ТОО «Поставщик {i}»", email=f"s{i}@sup.local")
                   for i, b in enumerate(VALID_BINS, 1)]
    CurrencyRate.objects.create(date=date.today() - timedelta(days=3), currency="USD", rate="500.0000")
    return w


def client_for(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


@pytest.fixture
def as_user():
    return client_for


def pdf_file(name="kp.pdf"):
    return SimpleUploadedFile(name, b"%PDF-1.4 test offer", content_type="application/pdf")


def create_analysis(w, *, items=(("product1", "10"),), approvers=("approver1", "approver2"), offers=True,
                    calculate=True, user=None):
    """Создаёт через API анализ, готовый к отправке на согласование."""
    c = client_for(user or w.marketer)
    r = c.post("/api/marketing-analyses/", {"dzo": w.emg.pk, "initiator_full_name": "Жумабаев Арман Болатович",
                                            "initiator_position": "Главный механик"}, format="json")
    assert r.status_code == 201, r.data
    aid = r.data["id"]
    item_ids = []
    for product_attr, qty in items:
        r = c.post(f"/api/marketing-analyses/{aid}/items/", {"nsi_product": getattr(w, product_attr).pk,
                                                             "quantity": qty, "delivery_place": "г. Атырау",
                                                             "delivery_term": "30 дней"}, format="json")
        assert r.status_code == 201, r.data
        item_ids.append(r.data["id"])
    if offers:
        for i, base in enumerate((1000, 1200)):
            prices = {str(item_id): str(base + n * 100) for n, item_id in enumerate(item_ids)}
            r = c.post(f"/api/marketing-analyses/{aid}/offers/", {
                "file": pdf_file(f"kp{i}.pdf"), "supplier_bin": VALID_BINS[i], "offer_date": date.today().isoformat(),
                "currency": "KZT", "vat_included": "false", "prices": __import__("json").dumps(prices)},
                format="multipart")
            assert r.status_code == 201, r.data
    if calculate:
        r = c.post(f"/api/marketing-analyses/{aid}/calculate/")
        assert r.status_code == 200, r.data
    if approvers:
        r = c.put(f"/api/marketing-analyses/{aid}/approvers/",
                  {"approvers": [getattr(w, a).pk for a in approvers]}, format="json")
        assert r.status_code == 200, r.data
    return aid, item_ids


def decide(user, aid, decision="approve", comment=""):
    return client_for(user).post(f"/api/marketing-analyses/{aid}/decision/",
                                 {"decision": decision, "comment": comment}, format="json")
