import importlib
import json
from unittest.mock import Mock
import pytest
from fastapi.testclient import TestClient

from api.server import app
from services.history_service import HistoryService
from schema.proposal_models import ProposalEvaluationReport


@pytest.fixture
def mock_engine_and_client(monkeypatch, tmp_path):
    api_mod = importlib.import_module("services.api_service")
    test_db = tmp_path / "test_history.db"
    test_history = HistoryService(db_path=test_db)
    monkeypatch.setattr(api_mod.api_service, "history", test_history)

    report = ProposalEvaluationReport(
        proposal_title="proposal.md",
        rfp_title="rfp.txt",
        overall_score_pct=85.0,
        executive_summary="Excellent proposal complying with all criteria.",
    )
    engine = Mock(return_value=report)
    monkeypatch.setattr(api_mod, "evaluate_proposal", engine)

    with TestClient(app) as client:
        yield client, engine, test_history


def test_health_check(mock_engine_and_client):
    client, _, _ = mock_engine_and_client
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"

    res_root = client.get("/health")
    assert res_root.status_code == 200


def test_evaluate_multipart_upload(mock_engine_and_client):
    client, engine, history = mock_engine_and_client
    custom_weights = {
        "problem_understanding": 10.0,
        "scope_deliverables_clarity": 20.0,
        "pricing_clarity": 30.0,
        "timeline_clarity": 15.0,
        "completeness_vs_rfp": 15.0,
        "tone_persuasiveness": 5.0,
        "risk_transparency": 5.0,
    }

    files = {
        "rfp_file": ("rfp.md", b"# Client RFP\nRequirements text"),
        "proposal_file": ("proposal.txt", b"Proposal draft text"),
    }
    data = {"weights": json.dumps(custom_weights)}

    response = client.post("/api/v1/evaluate", files=files, data=data)
    assert response.status_code == 200
    res_json = response.json()

    assert res_json["success"] is True
    assert res_json["history_id"] is not None
    assert "report" in res_json
    assert res_json["report"]["overall_score_pct"] == 85.0
    assert res_json["report"]["proposal_title"] == "proposal.md"
    assert res_json["report"]["rfp_title"] == "rfp.txt"

    # Verify record was stored in history db
    hist_record = history.get_evaluation_by_id(res_json["history_id"])
    assert hist_record is not None
    assert hist_record.overall_score_pct == 85.0


def test_history_crud_and_stats(mock_engine_and_client):
    client, _, history = mock_engine_and_client

    # Upload two evaluations
    files1 = {
        "rfp_file": ("nordframe_rfp.txt", b"RFP 1 content"),
        "proposal_file": ("nordframe_prop.md", b"Proposal 1 content"),
    }
    res1 = client.post("/api/v1/evaluate", files=files1)
    assert res1.status_code == 200
    id1 = res1.json()["history_id"]

    files2 = {
        "rfp_file": ("medicare_rfp.txt", b"RFP 2 content"),
        "proposal_file": ("medicare_prop.md", b"Proposal 2 content"),
    }
    res2 = client.post("/api/v1/evaluate", files=files2)
    assert res2.status_code == 200
    id2 = res2.json()["history_id"]

    # 1. Test List History
    list_res = client.get("/api/v1/history?limit=10")
    assert list_res.status_code == 200
    items = list_res.json()["items"]
    assert len(items) == 2
    assert list_res.json()["total_count"] == 2

    # 2. Test Get Detail
    detail_res = client.get(f"/api/v1/history/{id1}")
    assert detail_res.status_code == 200
    assert detail_res.json()["record"]["id"] == id1
    assert detail_res.json()["record"]["report"]["overall_score_pct"] == 85.0

    # 3. Test Stats
    stats_res = client.get("/api/v1/stats")
    assert stats_res.status_code == 200
    assert stats_res.json()["stats"]["total_evaluations"] == 2
    assert stats_res.json()["stats"]["average_score_pct"] == 85.0

    # 4. Test Delete One
    del_res = client.delete(f"/api/v1/history/{id1}")
    assert del_res.status_code == 200

    list_after_del = client.get("/api/v1/history")
    assert list_after_del.json()["total_count"] == 1

    # 5. Test Clear All
    clear_res = client.delete("/api/v1/history")
    assert clear_res.status_code == 200
    assert clear_res.json()["records_deleted"] == 1

    list_empty = client.get("/api/v1/history")
    assert list_empty.json()["total_count"] == 0


def test_invalid_weights_and_files(mock_engine_and_client):
    client, _, _ = mock_engine_and_client

    # Invalid weights
    files = {
        "rfp_file": ("rfp.txt", b"RFP"),
        "proposal_file": ("prop.txt", b"Prop"),
    }
    res = client.post("/api/v1/evaluate", files=files, data={"weights": "invalid_json"})
    assert res.status_code == 422

    # Unsupported file type
    files_unsupported = {
        "rfp_file": ("rfp.exe", b"binary"),
        "proposal_file": ("prop.txt", b"Prop"),
    }
    res_unsupported = client.post("/api/v1/evaluate", files=files_unsupported)
    assert res_unsupported.status_code == 415

    # Blank file
    files_blank = {
        "rfp_file": ("rfp.txt", b"   \n"),
        "proposal_file": ("prop.txt", b"Prop"),
    }
    res_blank = client.post("/api/v1/evaluate", files=files_blank)
    assert res_blank.status_code == 422
