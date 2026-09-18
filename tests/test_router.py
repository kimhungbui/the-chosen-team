import importlib
import json
from unittest.mock import Mock

import pymupdf
import pytest
from fastapi.testclient import TestClient

from router import api
from services.document_parser import parse_document
from schema.proposal_models import ProposalEvaluationReport


@pytest.fixture
def client_and_engine(monkeypatch):
    api_mod = importlib.import_module("services.api_service")
    report = ProposalEvaluationReport(
        proposal_title="proposal.md",
        rfp_title="rfp.txt",
        overall_score_pct=80,
        executive_summary="Ready for review",
        llm_error_traceback="private traceback",
    )
    engine = Mock(return_value=report)
    monkeypatch.setattr(api_mod, "evaluate_proposal", engine)
    with TestClient(api.app) as client:
        yield client, engine


def upload(client, rfp=("rfp.txt", b"Client requirements"), proposal=("proposal.md", b"Draft proposal")):
    return client.post("/evaluate", files={"rfp_file": rfp, "proposal_file": proposal})


def test_upload_returns_json(client_and_engine):
    client, engine = client_and_engine
    response = upload(client)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["success"] is True
    assert res_json["report"]["overall_score_pct"] == 80
    assert res_json["report"]["llm_error_traceback"] is None
    args = engine.call_args.kwargs
    assert args["rfp_text"] == "Client requirements"
    assert args["proposal_text"] == "Draft proposal"
    assert args["rfp_metrics"]["word_count"] == 2
    assert args["allow_fallback_on_error"] is True
    assert args["custom_weights"] == api.DEFAULT_WEIGHTS


def test_custom_weights_passed_to_engine(client_and_engine):
    client, engine = client_and_engine
    weights = {**api.DEFAULT_WEIGHTS, "pricing_clarity": 30, "problem_understanding": 0}
    response = client.post(
        "/evaluate",
        files={"rfp_file": ("rfp.txt", b"RFP"), "proposal_file": ("proposal.txt", b"Proposal")},
        data={"weights": json.dumps(weights)},
    )
    assert response.status_code == 200
    assert engine.call_args.kwargs["custom_weights"] == weights


@pytest.mark.parametrize("weights", [
    "not json", "null", "[]", "{}",
    json.dumps({**api.DEFAULT_WEIGHTS, "unknown": 0}),
    json.dumps({**api.DEFAULT_WEIGHTS, "pricing_clarity": -1}),
    json.dumps({**api.DEFAULT_WEIGHTS, "pricing_clarity": 101}),
    json.dumps({**api.DEFAULT_WEIGHTS, "pricing_clarity": 20}),
    json.dumps({**api.DEFAULT_WEIGHTS, "pricing_clarity": "15"}),
    json.dumps({**api.DEFAULT_WEIGHTS, "pricing_clarity": True}),
    json.dumps({**api.DEFAULT_WEIGHTS, "pricing_clarity": float("nan")}),
    json.dumps({**api.DEFAULT_WEIGHTS, "pricing_clarity": float("inf")}),
])
def test_invalid_weights_rejected(client_and_engine, weights):
    client, engine = client_and_engine
    response = client.post(
        "/evaluate",
        files={"rfp_file": ("rfp.txt", b"RFP"), "proposal_file": ("proposal.txt", b"Proposal")},
        data={"weights": weights},
    )
    assert response.status_code == 422
    engine.assert_not_called()


@pytest.mark.parametrize("filename,content,status", [
    ("rfp.txt", b" \n", 422),
    ("rfp.docx", b"document", 415),
    ("rfp.pdf", b"not a PDF", 422),
])
def test_invalid_upload(client_and_engine, filename, content, status):
    client, engine = client_and_engine
    assert upload(client, rfp=(filename, content)).status_code == status
    engine.assert_not_called()


def test_missing_file(client_and_engine):
    client, engine = client_and_engine
    response = client.post("/evaluate", files={"rfp_file": ("rfp.txt", b"RFP")})
    assert response.status_code == 422
    engine.assert_not_called()


def test_fallback_error_is_sanitized(client_and_engine):
    client, engine = client_and_engine
    engine.return_value.llm_error = "secret upstream details"
    engine.return_value.engine_notice = "secret upstream details"
    response = upload(client)
    assert response.status_code == 200
    assert "secret" not in response.text


@pytest.mark.parametrize("filename", ["document.txt", "document.MD"])
def test_text_parser(filename):
    text, metrics = parse_document(filename, b"  First line\nSecond line  ")
    assert text == "First line\nSecond line"
    assert metrics["count"] == 2
    assert metrics["word_count"] == 4


@pytest.mark.parametrize("width,height,label", [(595, 842, "Page"), (842, 595, "Slide")])
def test_pdf_parser(width, height, label):
    with pymupdf.open() as doc:
        page = doc.new_page(width=width, height=height)
        page.insert_text((72, 72), "Client requirements")
        content = doc.tobytes()
    text, metrics = parse_document("document.pdf", content)
    assert f"[{label} 1]" in text
    assert "Client requirements" in text
    assert metrics["count"] == 1


def test_blank_pdf(client_and_engine):
    client, engine = client_and_engine
    with pymupdf.open() as doc:
        doc.new_page()
        content = doc.tobytes()
    assert upload(client, rfp=("blank.pdf", content)).status_code == 422
    engine.assert_not_called()
