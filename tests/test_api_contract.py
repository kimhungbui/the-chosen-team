"""
Unit Tests for the API Contract Layer — Proposal Scorer.
Tests the ProposalScorerAPI Python service contract and the FastAPI REST endpoints.
"""

import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from schema.api_models import (
    EvaluateProposalRequest,
    EvaluateProposalResponse,
    HistoryListRequest,
    HistoryListResponse,
    HistoryDetailResponse,
    HistoryDeleteResponse,
    HistoryClearResponse,
    HistoryStatsResponse,
)
from schema.proposal_models import TrafficLight
from services.history_service import HistoryService
from services.api_service import ProposalScorerAPI
from api.server import app
from data.sample_data import SAMPLE_DATASETS


@pytest.fixture
def mock_api(tmp_path: Path) -> ProposalScorerAPI:
    """Create an isolated ProposalScorerAPI backed by a temporary SQLite database."""
    db_file = tmp_path / "test_api_history.db"
    history = HistoryService(db_path=db_file)
    return ProposalScorerAPI(history_backend=history)


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    """Create a FastAPI TestClient configured with isolated history backend."""
    from services.api_service import api_service
    db_file = tmp_path / "test_fastapi_history.db"
    api_service.history = HistoryService(db_path=db_file)
    return TestClient(app)


def test_evaluate_contract_deterministic(mock_api: ProposalScorerAPI):
    """Verify evaluating proposal via API contract with auto_save_history=True."""
    rfp_text = SAMPLE_DATASETS["rfp"]["content"]
    proposal_text = SAMPLE_DATASETS["proposals"]["response_3_strong"]["content"]

    req = EvaluateProposalRequest(
        rfp_text=rfp_text,
        proposal_text=proposal_text,
        proposal_title="High Quality Proposal",
        rfp_title="NordFrame RFP",
        use_llm_mode=False,  # deterministic fast evaluation
        auto_save_history=True,
        rfp_filename="rfp_nordframe.md",
        proposal_filename="response_3_strong.md",
    )

    resp: EvaluateProposalResponse = mock_api.evaluate(req)

    assert resp.success is True
    assert resp.report is not None
    assert resp.report.overall_score_pct > 70.0
    assert resp.history_id is not None
    assert resp.execution_time_ms > 0.0
    assert resp.engine_mode == "rule_engine"

    # Verify that it can immediately be retrieved via history list
    history_resp = mock_api.list_history()
    assert history_resp.success is True
    assert len(history_resp.items) == 1
    assert history_resp.items[0].id == resp.history_id
    assert history_resp.items[0].proposal_title == "High Quality Proposal"


def test_history_crud_contracts(mock_api: ProposalScorerAPI):
    """Verify list, detail, delete, stats, and clear contracts."""
    rfp_text = SAMPLE_DATASETS["rfp"]["content"]
    p_high = SAMPLE_DATASETS["proposals"]["response_3_strong"]["content"]
    p_low = SAMPLE_DATASETS["proposals"]["response_1_weak"]["content"]

    # 1. Evaluate two proposals
    r1 = mock_api.evaluate({
        "rfp_text": rfp_text,
        "proposal_text": p_high,
        "proposal_title": "High Run",
        "use_llm_mode": False,
        "auto_save_history": True,
    })
    r2 = mock_api.evaluate({
        "rfp_text": rfp_text,
        "proposal_text": p_low,
        "proposal_title": "Low Run",
        "use_llm_mode": False,
        "auto_save_history": True,
    })

    assert r1.history_id is not None
    assert r2.history_id is not None

    # 2. List history with filter
    list_res = mock_api.list_history(HistoryListRequest(search_query="High"))
    assert len(list_res.items) == 1
    assert list_res.items[0].id == r1.history_id

    # 3. Get Detail
    detail_res: HistoryDetailResponse = mock_api.get_history_detail(r1.history_id)
    assert detail_res.success is True
    assert detail_res.record is not None
    assert detail_res.record.id == r1.history_id
    assert len(detail_res.record.report.rubric_scores) == 7

    # 4. Get Stats
    stats_res: HistoryStatsResponse = mock_api.get_stats()
    assert stats_res.success is True
    assert stats_res.stats.total_evaluations == 2

    # 5. Delete Item
    del_res: HistoryDeleteResponse = mock_api.delete_history_item(r1.history_id)
    assert del_res.success is True
    assert del_res.deleted_id == r1.history_id

    # Check that deleted item is not found
    not_found = mock_api.get_history_detail(r1.history_id)
    assert not_found.success is False

    # 6. Clear All History
    clear_res: HistoryClearResponse = mock_api.clear_all_history()
    assert clear_res.success is True
    assert clear_res.records_deleted == 1
    assert len(mock_api.list_history().items) == 0


def test_fastapi_rest_endpoints(client: TestClient):
    """Verify REST API endpoints on FastAPI application."""
    # 1. Health check
    health = client.get("/api/v1/health")
    assert health.status_code == 200
    assert health.json()["status"] == "healthy"

    # 2. Evaluate endpoint
    eval_payload = {
        "rfp_text": SAMPLE_DATASETS["rfp"]["content"],
        "proposal_text": SAMPLE_DATASETS["proposals"]["response_3_strong"]["content"],
        "proposal_title": "API High Proposal",
        "rfp_title": "NordFrame API RFP",
        "use_llm_mode": False,
        "auto_save_history": True,
    }
    eval_resp = client.post("/api/v1/evaluate", json=eval_payload)
    assert eval_resp.status_code == 200
    eval_data = eval_resp.json()
    assert eval_data["success"] is True
    assert eval_data["history_id"] is not None
    rec_id = eval_data["history_id"]

    # 3. List history endpoint
    hist_resp = client.get("/api/v1/history")
    assert hist_resp.status_code == 200
    hist_data = hist_resp.json()
    assert hist_data["success"] is True
    assert len(hist_data["items"]) >= 1

    # 4. Detail endpoint
    det_resp = client.get(f"/api/v1/history/{rec_id}")
    assert det_resp.status_code == 200
    det_data = det_resp.json()
    assert det_data["success"] is True
    assert det_data["record"]["id"] == rec_id

    # 5. Stats endpoint
    stats_resp = client.get("/api/v1/stats")
    assert stats_resp.status_code == 200
    assert stats_resp.json()["stats"]["total_evaluations"] >= 1

    # 6. Delete endpoint
    del_resp = client.delete(f"/api/v1/history/{rec_id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["success"] is True

    # 7. 404 for deleted record
    missing_resp = client.get(f"/api/v1/history/{rec_id}")
    assert missing_resp.status_code == 404
