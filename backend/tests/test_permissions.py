"""Матрица доступа (раздел 4): видимость и действия по ролям; чужой анализ по ID → 404."""

import pytest

from apps.marketing_analysis.models import Status
from tests.conftest import client_for, create_analysis, decide

pytestmark = pytest.mark.django_db


def ids(user, **params):
    r = client_for(user).get("/api/marketing-analyses/", params)
    assert r.status_code == 200
    return {row["id"] for row in r.data["results"]}


def test_visibility_by_role(world):
    w = world
    aid, _ = create_analysis(w)  # ДЗО EMG, согласующие approver1, approver2
    assert aid in ids(w.marketer)
    assert aid in ids(w.marketer2)  # маркетолог того же ДЗО
    assert aid not in ids(w.marketer_mmg)  # маркетолог другого ДЗО
    assert aid in ids(w.approver1)  # участник маршрута
    assert aid not in ids(w.outsider)  # сотрудник ДЗО без участия
    assert aid in ids(w.db_spec) and aid in ids(w.db_dir) and aid in ids(w.admin)


@pytest.mark.parametrize("who", ["marketer_mmg", "outsider", "approver_mmg"])
def test_foreign_analysis_by_id_is_404(world, who):
    w = world
    aid, item_ids = create_analysis(w)
    c = client_for(getattr(w, who))
    assert c.get(f"/api/marketing-analyses/{aid}/").status_code == 404
    assert c.get(f"/api/marketing-analyses/{aid}/history/").status_code == 404
    assert c.get(f"/api/marketing-analyses/{aid}/analytics/").status_code == 404
    assert c.post(f"/api/marketing-analyses/{aid}/decision/", {"decision": "approve"}, format="json").status_code == 404
    assert c.patch(f"/api/marketing-analyses/{aid}/items/{item_ids[0]}/", {"quantity": 1},
                   format="json").status_code == 404


def test_only_marketer_creates_and_only_for_own_dzo(world):
    w = world
    payload = {"dzo": w.emg.pk, "initiator_full_name": "Иванов"}
    for user in (w.approver1, w.db_spec, w.db_dir):
        assert client_for(user).post("/api/marketing-analyses/", payload, format="json").status_code == 403
    r = client_for(w.marketer_mmg).post("/api/marketing-analyses/", payload, format="json")
    assert r.status_code == 403
    r = client_for(w.marketer).post("/api/marketing-analyses/", {"initiator_full_name": "Иванов"}, format="json")
    assert r.status_code == 201 and r.data["dzo"]["code"] == "EMG"  # ДЗО пользователя по умолчанию


def test_non_marketers_cannot_edit(world):
    w = world
    aid, item_ids = create_analysis(w, calculate=False)
    for user in (w.approver1, w.db_spec, w.db_dir):
        c = client_for(user)
        assert c.post(f"/api/marketing-analyses/{aid}/calculate/").status_code == 403
        assert c.patch(f"/api/marketing-analyses/{aid}/items/{item_ids[0]}/", {"quantity": 1},
                       format="json").status_code == 403
        assert c.post(f"/api/marketing-analyses/{aid}/submit/").status_code == 403
        r = c.get(f"/api/marketing-analyses/{aid}/")
        assert r.status_code == 200 and r.data["available_actions"] == []


def test_decisions_only_by_current_executor(world):
    w = world
    aid, _ = create_analysis(w)
    client_for(w.marketer).post(f"/api/marketing-analyses/{aid}/submit/")
    # этап 1: по очереди — сначала approver1
    for user in (w.approver2, w.db_spec, w.db_dir, w.marketer, w.admin):
        assert decide(user, aid).status_code == 403, user.username
    r = client_for(w.approver1).get(f"/api/marketing-analyses/{aid}/")
    assert set(r.data["available_actions"]) == {"approve", "rework"}
    assert decide(w.approver1, aid).status_code == 200
    assert decide(w.approver1, aid).status_code == 403  # свой шаг уже пройден
    decide(w.approver2, aid)
    # этап 2 — только специалист ДБ
    assert decide(w.db_dir, aid).status_code == 403
    assert decide(w.db_spec, aid).status_code == 200
    # этап 3 — только директор ДБ
    assert decide(w.db_spec, aid).status_code == 403
    assert decide(w.db_dir, aid).status_code == 200


def test_awaiting_me_tab_and_counts(world):
    w = world
    aid, _ = create_analysis(w)
    create_analysis(w)
    client_for(w.marketer).post(f"/api/marketing-analyses/{aid}/submit/")
    r = client_for(w.approver1).get("/api/marketing-analyses/", {"tab": "awaiting_me"})
    assert [row["id"] for row in r.data["results"]] == [aid]
    assert r.data["counts"]["awaiting_me"] == 1
    r = client_for(w.marketer).get("/api/marketing-analyses/")
    assert r.data["counts"]["on_approval"] == 1 and r.data["counts"]["collecting_kp"] == 1
    assert r.data["counts"]["all"] == 2
    assert ids(w.approver2, tab="awaiting_me") == set()  # его очередь ещё не наступила
    assert ids(w.db_spec, tab="awaiting_me") == set()


def test_approvers_must_be_from_analysis_dzo(world):
    w = world
    aid, _ = create_analysis(w, approvers=())
    c = client_for(w.marketer)
    r = c.put(f"/api/marketing-analyses/{aid}/approvers/", {"approvers": [w.approver_mmg.pk]}, format="json")
    assert r.status_code == 400 and r.data["errors"][0]["code"] == "other_dzo"
    r = c.put(f"/api/marketing-analyses/{aid}/approvers/", {"approvers": [w.marketer.pk]}, format="json")
    assert r.status_code == 400 and r.data["errors"][0]["code"] == "author"
    r = c.put(f"/api/marketing-analyses/{aid}/approvers/", {"approvers": [w.approver2.pk, w.approver1.pk]},
              format="json")
    assert r.status_code == 200
    assert [a["user"]["id"] for a in r.data["approvers"]] == [w.approver2.pk, w.approver1.pk]


def test_pdf_download_rights(world):
    w = world
    aid, _ = create_analysis(w, approvers=("approver1",))
    client_for(w.marketer).post(f"/api/marketing-analyses/{aid}/submit/")
    for user in (w.approver1, w.db_spec, w.db_dir):
        decide(user, aid)
    for user in (w.marketer, w.approver1, w.db_spec, w.db_dir, w.admin):
        r = client_for(user).get(f"/api/marketing-analyses/{aid}/conclusion.pdf")
        assert r.status_code == 200, user.username
    assert client_for(w.outsider).get(f"/api/marketing-analyses/{aid}/conclusion.pdf").status_code == 404
    assert client_for(w.marketer_mmg).get(f"/api/marketing-analyses/{aid}/conclusion.pdf").status_code == 404


def test_feature_flag_disables_api(world, settings):
    settings.MA_ENABLED = False
    assert client_for(world.marketer).get("/api/marketing-analyses/").status_code == 404
    r = client_for(world.marketer).get("/api/auth/me/")
    assert r.data["features"]["marketing_analysis"] is False


def test_anonymous_denied(world):
    from rest_framework.test import APIClient

    assert APIClient().get("/api/marketing-analyses/").status_code == 403


def test_status_tabs_filters(world):
    w = world
    aid, _ = create_analysis(w)
    client_for(w.marketer).post(f"/api/marketing-analyses/{aid}/cancel/")
    assert ids(w.marketer, tab="cancelled") == {aid}
    assert ids(w.marketer, tab="draft") == set()
    assert ids(w.marketer, nsi_code="1010") == {aid}
    assert ids(w.marketer, nsi_code="9999") == set()
    assert Status.CANCELLED == client_for(w.marketer).get(f"/api/marketing-analyses/{aid}/").data["status"]
