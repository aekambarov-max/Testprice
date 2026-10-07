"""State machine: разрешённые и запрещённые переходы, маршрут, повторная отправка, валидации."""

import pytest

from apps.core.models import AuditLog, Notification
from apps.marketing_analysis.models import ApprovalStep, MarketingAnalysis, PdfStatus, Status
from apps.marketing_analysis.workflow import TRANSITIONS
from apps.pricing.models import PriceCatalogEntry
from tests.conftest import client_for, create_analysis, decide

pytestmark = pytest.mark.django_db


def status_of(aid):
    return MarketingAnalysis.objects.get(pk=aid).status


def submit(w, aid, user=None):
    return client_for(user or w.marketer).post(f"/api/marketing-analyses/{aid}/submit/")


def test_full_path_draft_to_approved_with_pdf_and_catalog(world):
    w = world
    aid, _ = create_analysis(w)
    assert status_of(aid) == Status.COLLECTING_KP  # первое КП переводит черновик в «Сбор КП»
    analysis = MarketingAnalysis.objects.get(pk=aid)
    assert analysis.number.startswith("ID") and ".EMG." in analysis.number

    r = submit(w, aid)
    assert r.status_code == 200, r.data
    assert r.data["status"] == Status.ON_APPROVAL_DZO
    assert [s["assignee"] for s in r.data["route"]][:2] == ["Approver1 Тест", "Approver2 Тест"]

    assert decide(w.approver1, aid).status_code == 200
    assert status_of(aid) == Status.ON_APPROVAL_DZO  # второй согласующий этапа 1
    assert decide(w.approver2, aid, comment="Согласен").status_code == 200
    assert status_of(aid) == Status.ON_APPROVAL_DB
    assert decide(w.db_spec, aid).status_code == 200
    assert status_of(aid) == Status.ON_FINAL_APPROVAL
    r = decide(w.db_dir, aid, comment="Утверждаю")
    assert r.status_code == 200
    assert r.data["status"] == Status.APPROVED
    assert "download_pdf" in r.data["available_actions"]

    analysis.refresh_from_db()
    assert analysis.pdf_status == PdfStatus.READY and len(analysis.pdf_sha256) == 64
    entry = PriceCatalogEntry.objects.get(source_type="marketing_analysis", source_id=str(aid))
    assert entry.is_active and entry.price_wo_vat == analysis.items.first().marketing_price

    actions = list(AuditLog.objects.filter(object_id=str(aid)).values_list("action", flat=True))
    for expected in ("created", "item_added", "offer_uploaded", "calculated", "approvers_set", "submitted",
                     "step_approved", "approved"):
        assert expected in actions
    approved_log = AuditLog.objects.get(object_id=str(aid), action="approved")
    assert approved_log.from_status == Status.ON_FINAL_APPROVAL and approved_log.to_status == Status.APPROVED
    assert approved_log.user == w.db_dir and approved_log.ip_address == "127.0.0.1"

    assert Notification.objects.filter(user=w.approver1, event="ma_step_assigned").exists()
    assert Notification.objects.filter(user=w.db_spec, event="ma_step_assigned").exists()
    assert Notification.objects.filter(user=w.marketer, event="ma_approved").exists()
    assert Notification.objects.filter(user=w.marketer, event="ma_pdf_ready").exists()


def test_rework_restarts_route_from_stage_one(world):
    w = world
    aid, _ = create_analysis(w)
    submit(w, aid)
    decide(w.approver1, aid)
    decide(w.approver2, aid)
    r = decide(w.db_spec, aid, "rework", "Обоснуйте цену")
    assert r.status_code == 200 and r.data["status"] == Status.REWORK
    assert Notification.objects.filter(user=w.marketer, event="ma_returned", body__contains="Обоснуйте").exists()
    # оставшийся шаг итерации помечен как не рассматривавшийся
    assert ApprovalStep.objects.filter(analysis_id=aid, iteration=1, status="skipped").count() == 1

    r = submit(w, aid)
    assert r.status_code == 200 and r.data["status"] == Status.ON_APPROVAL_DZO
    assert r.data["iteration"] == 2
    current = ApprovalStep.objects.get(analysis_id=aid, iteration=2, status="pending")
    assert current.stage == 1 and current.assignee_user == w.approver1


def test_rework_without_restart_resumes_from_returning_stage(world, settings):
    settings.MA_RESTART_ROUTE_FROM_BEGINNING = False
    w = world
    aid, _ = create_analysis(w)
    submit(w, aid)
    decide(w.approver1, aid)
    decide(w.approver2, aid)
    decide(w.db_spec, aid)
    decide(w.db_dir, aid, "rework", "Уточнить курс")
    r = submit(w, aid)
    assert r.status_code == 200 and r.data["status"] == Status.ON_FINAL_APPROVAL


def test_rework_requires_comment(world):
    w = world
    aid, _ = create_analysis(w)
    submit(w, aid)
    r = decide(w.approver1, aid, "rework", "   ")
    assert r.status_code == 400 and r.data["code"] == "comment_required"
    assert status_of(aid) == Status.ON_APPROVAL_DZO


def test_submit_validation_errors(world):
    w = world
    aid, _ = create_analysis(w, offers=False, calculate=False, approvers=())
    client_for(w.marketer).post(f"/api/marketing-analyses/{aid}/start-collecting/")
    r = submit(w, aid)
    assert r.status_code == 400 and r.data["code"] == "validation_failed"
    codes = {e["code"] for e in r.data["errors"]}
    assert {"not_enough_offers", "price_not_calculated", "approvers_required"} <= codes


def test_submit_requires_min_kp_count(world, settings):
    settings.MA_MIN_KP_COUNT = 3
    aid, _ = create_analysis(world)
    r = submit(world, aid)
    assert r.status_code == 400
    assert any(e["code"] == "not_enough_offers" for e in r.data["errors"])


def test_new_offer_invalidates_calculated_price(world):
    w = world
    aid, item_ids = create_analysis(w)
    from tests.conftest import VALID_BINS, pdf_file
    import json
    from datetime import date

    client_for(w.marketer).post(f"/api/marketing-analyses/{aid}/offers/", {
        "file": pdf_file(), "supplier_bin": VALID_BINS[2], "offer_date": date.today().isoformat(),
        "currency": "KZT", "prices": json.dumps({str(item_ids[0]): "900"})}, format="multipart")
    r = submit(w, aid)
    assert r.status_code == 400
    assert any(e["code"] == "price_not_calculated" for e in r.data["errors"])


def test_submit_without_approvers_when_allowed_goes_to_db(world, settings):
    settings.MA_ALLOW_SKIP_DZO_STAGE = True
    aid, _ = create_analysis(world, approvers=())
    r = submit(world, aid)
    assert r.status_code == 200 and r.data["status"] == Status.ON_APPROVAL_DB


def test_draft_cannot_be_submitted_directly(world):
    w = world
    r = client_for(w.marketer).post("/api/marketing-analyses/", {"dzo": w.emg.pk, "initiator_full_name": "Иванов"},
                                    format="json")
    r = submit(w, r.data["id"])
    assert r.status_code == 409 and r.data["code"] == "status_changed"


def test_editing_forbidden_after_submit(world):
    w = world
    aid, item_ids = create_analysis(w)
    submit(w, aid)
    c = client_for(w.marketer)
    assert c.patch(f"/api/marketing-analyses/{aid}/items/{item_ids[0]}/", {"quantity": "5"},
                   format="json").status_code == 409
    assert c.post(f"/api/marketing-analyses/{aid}/items/", {"nsi_product": w.product2.pk, "quantity": "1"},
                  format="json").status_code == 409
    assert c.post(f"/api/marketing-analyses/{aid}/calculate/").status_code == 409
    assert c.patch(f"/api/marketing-analyses/{aid}/", {"initiator_full_name": "X"}, format="json").status_code == 409
    assert c.post(f"/api/marketing-analyses/{aid}/cancel/").status_code == 409
    assert c.put(f"/api/marketing-analyses/{aid}/approvers/", {"approvers": [w.approver1.pk]},
                 format="json").status_code == 409


def test_cancel_and_terminal_states(world):
    w = world
    aid, _ = create_analysis(w)
    r = client_for(w.marketer).post(f"/api/marketing-analyses/{aid}/cancel/", {"comment": "Потребность снята"},
                                    format="json")
    assert r.status_code == 200 and r.data["status"] == Status.CANCELLED
    assert submit(w, aid).status_code == 409
    assert client_for(w.marketer).post(f"/api/marketing-analyses/{aid}/cancel/").status_code == 409


def test_approved_is_terminal(world):
    w = world
    aid, _ = create_analysis(w, approvers=("approver1",))
    submit(w, aid)
    for user in (w.approver1, w.db_spec, w.db_dir):
        decide(user, aid)
    assert status_of(aid) == Status.APPROVED
    assert decide(w.db_dir, aid).status_code == 409
    assert client_for(w.marketer).post(f"/api/marketing-analyses/{aid}/cancel/").status_code == 409


def test_transition_table_matches_spec():
    S = Status
    assert TRANSITIONS[S.DRAFT] == {S.COLLECTING_KP, S.CANCELLED}
    assert TRANSITIONS[S.ON_APPROVAL_DZO] == {S.ON_APPROVAL_DB, S.REWORK}
    assert TRANSITIONS[S.ON_APPROVAL_DB] == {S.ON_FINAL_APPROVAL, S.REWORK}
    assert TRANSITIONS[S.ON_FINAL_APPROVAL] == {S.APPROVED, S.REWORK}
    assert TRANSITIONS[S.APPROVED] == set() and TRANSITIONS[S.CANCELLED] == set()


def test_delete_only_in_draft(world):
    w = world
    c = client_for(w.marketer)
    draft = c.post("/api/marketing-analyses/", {"dzo": w.emg.pk, "initiator_full_name": "Иванов"}, format="json")
    assert c.delete(f"/api/marketing-analyses/{draft.data['id']}/").status_code == 204
    aid, _ = create_analysis(w)
    assert c.delete(f"/api/marketing-analyses/{aid}/").status_code == 409
