import hashlib
import io
import threading
from unittest import mock

import pytest
from django.db import connection, connections
from pypdf import PdfReader

from apps.core.models import AuditLog
from apps.marketing_analysis.models import ApprovalStep, MarketingAnalysis, PdfStatus, Status
from tests.conftest import client_for, create_analysis, decide


def approve_all(w, aid, users):
    client_for(w.marketer).post(f"/api/marketing-analyses/{aid}/submit/")
    for user in users:
        assert decide(user, aid, comment=f"ok {user.username}").status_code == 200


@pytest.mark.django_db
def test_pdf_contains_number_items_and_approval_sheet(world):
    w = world
    aid, _ = create_analysis(w, items=(("product1", "10"), ("product2", "2")))
    client_for(w.marketer).patch(f"/api/marketing-analyses/{aid}/", {"price_justification": "Ңғүұқөһ әі тест"},
                                 format="json")
    approve_all(w, aid, [w.approver1, w.approver2, w.db_spec, w.db_dir])
    analysis = MarketingAnalysis.objects.get(pk=aid)
    assert analysis.pdf_status == PdfStatus.READY

    r1 = client_for(w.marketer).get(f"/api/marketing-analyses/{aid}/conclusion.pdf")
    body1 = b"".join(r1.streaming_content)
    assert r1["Content-Type"] == "application/pdf"
    assert "Маркетинговое_заключение_" in __import__("urllib.parse").parse.unquote(r1["Content-Disposition"])
    assert hashlib.sha256(body1).hexdigest() == analysis.pdf_sha256 == r1["X-Content-SHA256"]

    text = "\n".join(page.extract_text() for page in PdfReader(io.BytesIO(body1)).pages)
    assert analysis.number in text
    assert "Труба стальная 89х6" in text and "Насос НН2Б-44" in text
    assert "Лист согласования" in text and "УТВЕРЖДЕНО" in text
    assert "Ңғүұқөһ" in text  # казахские буквы встроенным шрифтом
    assert "Approver1" in text and "Dbdir" in text

    # повторное скачивание отдаёт тот же файл; повторный запуск генерации не меняет его
    from apps.marketing_analysis.tasks import generate_conclusion_pdf

    generate_conclusion_pdf(aid)
    r2 = client_for(w.db_dir).get(f"/api/marketing-analyses/{aid}/conclusion.pdf")
    assert hashlib.sha256(b"".join(r2.streaming_content)).hexdigest() == analysis.pdf_sha256
    assert AuditLog.objects.filter(object_id=str(aid), action="pdf_downloaded").count() == 2


@pytest.mark.django_db
def test_pdf_not_available_before_approval(world):
    aid, _ = create_analysis(world)
    assert client_for(world.marketer).get(f"/api/marketing-analyses/{aid}/conclusion.pdf").status_code == 404


@pytest.mark.django_db
def test_pdf_failure_does_not_roll_back_approval(world):
    w = world
    aid, _ = create_analysis(w, approvers=("approver1",))
    with mock.patch("apps.marketing_analysis.tasks.render_conclusion_pdf", side_effect=RuntimeError("boom")):
        approve_all(w, aid, [w.approver1, w.db_spec, w.db_dir])
    analysis = MarketingAnalysis.objects.get(pk=aid)
    assert analysis.status == Status.APPROVED and analysis.pdf_status == PdfStatus.FAILED
    r = client_for(w.marketer).get(f"/api/marketing-analyses/{aid}/conclusion.pdf")
    assert r.status_code == 409 and r.data["pdf_status"] == PdfStatus.FAILED
    # повторный запуск — только администратор и только после ошибки
    assert client_for(w.marketer).post(f"/api/marketing-analyses/{aid}/regenerate-pdf/").status_code == 403
    assert "regenerate_pdf" in client_for(w.admin).get(f"/api/marketing-analyses/{aid}/").data["available_actions"]
    r = client_for(w.admin).post(f"/api/marketing-analyses/{aid}/regenerate-pdf/")
    assert r.status_code == 200 and r.data["pdf_status"] == PdfStatus.READY
    assert client_for(w.admin).post(f"/api/marketing-analyses/{aid}/regenerate-pdf/").status_code == 409


@pytest.mark.django_db
def test_notification_failure_does_not_roll_back_status(world):
    w = world
    aid, _ = create_analysis(w)
    with mock.patch("apps.core.tasks.deliver_notification.delay", side_effect=ConnectionError("redis down")):
        r = client_for(w.marketer).post(f"/api/marketing-analyses/{aid}/submit/")
    assert r.status_code == 200
    assert MarketingAnalysis.objects.get(pk=aid).status == Status.ON_APPROVAL_DZO


@pytest.mark.django_db
def test_double_click_on_same_step_only_one_passes(world):
    """Повторное решение по уже обработанному шагу (двойное нажатие / устаревшая страница) → 409."""
    w = world
    aid, _ = create_analysis(w, approvers=("approver1",))
    client_for(w.marketer).post(f"/api/marketing-analyses/{aid}/submit/")
    step_id = client_for(w.approver1).get(f"/api/marketing-analyses/{aid}/").data["current_step_id"]
    payload = {"decision": "approve", "step_id": step_id}
    c = client_for(w.approver1)
    assert c.post(f"/api/marketing-analyses/{aid}/decision/", payload, format="json").status_code == 200
    # специалист ДБ видел страницу со старым шагом
    r = client_for(w.db_spec).post(f"/api/marketing-analyses/{aid}/decision/", payload, format="json")
    assert r.status_code == 409 and r.data["code"] == "step_already_processed"
    assert ApprovalStep.objects.filter(analysis_id=aid, status="approved").count() == 1


@pytest.mark.django_db(transaction=True, serialized_rollback=True)
@pytest.mark.skipif(connection.vendor != "postgresql", reason="Нужен PostgreSQL (select_for_update)")
def test_concurrent_decisions_only_one_passes(world):
    """Два одновременных решения по одному шагу (роль ДБ: два специалиста) — проходит только одно."""
    from apps.core import roles
    from django.contrib.auth.models import Group
    from tests.conftest import make_user

    w = world
    second_spec = make_user("dbspec2", w.kmg, [roles.DB_SPECIALIST])
    aid, _ = create_analysis(w, approvers=("approver1",))
    client_for(w.marketer).post(f"/api/marketing-analyses/{aid}/submit/")
    decide(w.approver1, aid)
    step_id = ApprovalStep.objects.get(analysis_id=aid, status="pending").pk

    barrier = threading.Barrier(2)
    results = []

    def run(user):
        try:
            barrier.wait()
            r = client_for(user).post(f"/api/marketing-analyses/{aid}/decision/",
                                      {"decision": "approve", "step_id": step_id}, format="json")
            results.append(r.status_code)
        finally:
            connections.close_all()

    threads = [threading.Thread(target=run, args=(u,)) for u in (w.db_spec, second_spec)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert sorted(results) == [200, 409]
    assert MarketingAnalysis.objects.get(pk=aid).status == Status.ON_FINAL_APPROVAL
    assert ApprovalStep.objects.filter(analysis_id=aid, stage=2, status="approved").count() == 1
    assert Group.objects.filter(name=roles.DB_SPECIALIST).exists()
