"""
Unit tests for the HistoryService backend storage and analytics.
Tests SQLite persistence, querying, search filtering, pagination, deletion, and aggregate statistics.
"""

import json
import pytest
from pathlib import Path

from schema.proposal_models import (
    ProposalEvaluationReport,
    CriterionScore,
    RequirementGap,
    AmbiguousRequirement,
    TrafficLight,
    RequirementCoverageStatus,
)
from schema.history_models import (
    HistoryRecordSummary,
    HistoryRecordDetail,
    HistoryStats,
)
from services.history_service import HistoryService


def make_dummy_report(
    proposal_title: str = "Test Proposal Alpha",
    rfp_title: str = "Client RFP Alpha",
    score_pct: float = 84.5,
    traffic_light: TrafficLight = TrafficLight.GREEN,
    engine_mode: str = "agno_llm",
) -> ProposalEvaluationReport:
    """Helper to create a realistic mock ProposalEvaluationReport for testing."""
    return ProposalEvaluationReport(
        proposal_title=proposal_title,
        rfp_title=rfp_title,
        detected_client_priorities="Fast delivery and compliance",
        overall_score_pct=score_pct,
        overall_traffic_light=traffic_light,
        executive_summary="Solid proposal with strong technical coverage.",
        rubric_scores=[
            CriterionScore(
                criterion_id="problem_understanding",
                criterion_name="Problem Understanding",
                score_1_to_5=4.5,
                weight=15.0,
                weighted_score=13.5,
                traffic_light=TrafficLight.GREEN,
                rationale="Grasps warehouse automation pain points clearly.",
                score_factors_high=["Clear pain point description", "Specific operational metrics"],
                score_factors_low=[],
                citations=[],
                suggested_fixes=[],
            ),
            CriterionScore(
                criterion_id="pricing_clarity",
                criterion_name="Pricing Clarity",
                score_1_to_5=3.5,
                weight=20.0,
                weighted_score=14.0,
                traffic_light=TrafficLight.YELLOW,
                rationale="Itemized rates provided, but travel expenses unestimated.",
                score_factors_high=["Transparent hourly rates"],
                score_factors_low=["Travel expenses not capped"],
                citations=[],
                suggested_fixes=["Add cap on travel expenses"],
            ),
        ],
        requirement_gaps=[
            RequirementGap(
                requirement_id="REQ-02",
                requirement_title="SLA Response Time",
                status=RequirementCoverageStatus.PARTIAL_GAP,
                rfp_snippet="Vendor must guarantee 4-hour critical issue response time.",
                proposal_snippet="Vendor will respond promptly to support requests.",
                issue_description="Lacks guaranteed SLA hours.",
                placement_anchor="Section 4 Support Services",
                priority_level="HIGH",
                actionable_rewrite="FPT guarantees 4-hour response time for P1 critical tickets.",
            )
        ],
        ambiguous_requirements=[
            AmbiguousRequirement(
                requirement_id="REQ-05",
                requirement_title="Real-time Synchronization",
                rfp_snippet="System must synchronize data in real time.",
                ambiguity_reason="Missing latency SLA threshold.",
                proposal_handling="HANDLED_WITH_ASSUMPTIONS",
                clarification_question="What is the allowable latency threshold for synchronization?",
                recommended_assumption="Assumes sub-second synchronization under standard network conditions.",
            )
        ],
        top_strengths=["Strong team credentials", "Direct experience in industry"],
        top_risks_and_remediations=["Vague SLA response times"],
        engine_mode=engine_mode,
    )


@pytest.fixture
def temp_service(tmp_path: Path) -> HistoryService:
    """Provides an isolated HistoryService backed by a temporary SQLite database."""
    db_file = tmp_path / "test_history.db"
    return HistoryService(db_path=db_file)


def test_init_and_table_creation(temp_service: HistoryService):
    """Verify database and tables are created upon initialization."""
    assert temp_service.db_path.exists()
    stats = temp_service.get_stats()
    assert stats.total_evaluations == 0
    assert stats.average_score_pct == 0.0


def test_save_and_retrieve_evaluation(temp_service: HistoryService):
    """Verify saving a full ProposalEvaluationReport and retrieving it by ID."""
    report = make_dummy_report(
        proposal_title="Warehouse System Proposal",
        rfp_title="Logistics RFP 2026",
        score_pct=88.2,
        traffic_light=TrafficLight.GREEN,
    )
    weights = {"problem_understanding": 20.0, "pricing_clarity": 20.0}
    metadata = {"auditor": "Senior Reviewer", "version": "v1.2"}

    saved = temp_service.save_evaluation(
        report=report,
        weights=weights,
        rfp_filename="logistics_rfp.md",
        proposal_filename="warehouse_proposal.pdf",
        metadata=metadata,
        record_id="eval_test_001",
    )

    assert saved.id == "eval_test_001"
    assert saved.rfp_title == "Logistics RFP 2026"
    assert saved.proposal_title == "Warehouse System Proposal"
    assert saved.overall_score_pct == 88.2
    assert saved.overall_traffic_light == TrafficLight.GREEN
    assert saved.rfp_filename == "logistics_rfp.md"
    assert saved.proposal_filename == "warehouse_proposal.pdf"
    assert saved.weights == weights
    assert saved.metadata == metadata

    # Retrieve by ID
    retrieved = temp_service.get_evaluation_by_id("eval_test_001")
    assert retrieved is not None
    assert retrieved.id == "eval_test_001"
    assert len(retrieved.report.rubric_scores) == 2
    assert retrieved.report.rubric_scores[0].criterion_id == "problem_understanding"
    assert len(retrieved.report.requirement_gaps) == 1
    assert retrieved.report.requirement_gaps[0].requirement_id == "REQ-02"
    assert len(retrieved.report.ambiguous_requirements) == 1
    assert retrieved.report.ambiguous_requirements[0].requirement_id == "REQ-05"


def test_save_from_dict(temp_service: HistoryService):
    """Verify saving from raw dictionary report payload."""
    report_obj = make_dummy_report(proposal_title="Dict Proposal", score_pct=60.0, traffic_light=TrafficLight.YELLOW)
    report_dict = report_obj.model_dump()

    saved = temp_service.save_evaluation(
        report=report_dict,
        record_id="eval_dict_01",
    )
    assert saved.id == "eval_dict_01"
    assert saved.proposal_title == "Dict Proposal"
    assert saved.overall_score_pct == 60.0
    assert saved.overall_traffic_light == TrafficLight.YELLOW


def test_list_history_and_pagination(temp_service: HistoryService):
    """Verify listing history summaries with limit, offset, and correct ordering."""
    for i in range(5):
        rep = make_dummy_report(
            proposal_title=f"Proposal {i}",
            rfp_title=f"RFP {i}",
            score_pct=50.0 + i * 10,
        )
        temp_service.save_evaluation(
            report=rep,
            record_id=f"rec_{i}",
            timestamp=f"2026-09-18T10:0{i}:00Z",
        )

    # All 5 records
    history = temp_service.get_history(limit=10)
    assert len(history) == 5
    # Descending order by timestamp: rec_4 should be first
    assert history[0].id == "rec_4"
    assert history[-1].id == "rec_0"

    # Pagination: limit 2, offset 1
    page = temp_service.get_history(limit=2, offset=1)
    assert len(page) == 2
    assert page[0].id == "rec_3"
    assert page[1].id == "rec_2"


def test_search_and_filter(temp_service: HistoryService):
    """Verify search filtering by text and traffic light status."""
    temp_service.save_evaluation(
        report=make_dummy_report(
            proposal_title="Fintech Billing Engine",
            rfp_title="Bank RFP",
            score_pct=92.0,
            traffic_light=TrafficLight.GREEN,
            engine_mode="agno_llm",
        ),
        record_id="fintech_01",
        rfp_filename="bank_rfp.pdf",
    )
    temp_service.save_evaluation(
        report=make_dummy_report(
            proposal_title="Healthcare Patient Portal",
            rfp_title="Hospital RFP",
            score_pct=45.0,
            traffic_light=TrafficLight.RED,
            engine_mode="rule_engine",
        ),
        record_id="health_01",
        rfp_filename="hospital_rfp.docx",
    )

    # Search by keyword
    fintech_matches = temp_service.get_history(search_query="fintech")
    assert len(fintech_matches) == 1
    assert fintech_matches[0].id == "fintech_01"

    # Search by filename
    filename_matches = temp_service.get_history(search_query="hospital")
    assert len(filename_matches) == 1
    assert filename_matches[0].id == "health_01"

    # Filter by traffic light
    reds = temp_service.get_history(traffic_light=TrafficLight.RED)
    assert len(reds) == 1
    assert reds[0].id == "health_01"

    # Filter by engine mode
    rule_runs = temp_service.get_history(engine_mode="rule_engine")
    assert len(rule_runs) == 1
    assert rule_runs[0].id == "health_01"


def test_delete_and_clear_history(temp_service: HistoryService):
    """Verify deleting a single record and clearing entire history."""
    temp_service.save_evaluation(make_dummy_report(), record_id="del_1")
    temp_service.save_evaluation(make_dummy_report(), record_id="del_2")

    # Delete existing
    deleted = temp_service.delete_evaluation("del_1")
    assert deleted is True
    assert temp_service.get_evaluation_by_id("del_1") is None

    # Delete non-existing
    assert temp_service.delete_evaluation("non_existent") is False

    # Clear remaining
    cleared_count = temp_service.clear_history()
    assert cleared_count == 1
    assert len(temp_service.get_history()) == 0


def test_aggregate_stats(temp_service: HistoryService):
    """Verify aggregate statistics calculation across varied evaluation runs."""
    # Add 1 GREEN (90.0), 1 YELLOW (70.0), 1 RED (40.0)
    temp_service.save_evaluation(
        make_dummy_report(score_pct=90.0, traffic_light=TrafficLight.GREEN),
        record_id="stat_g",
    )
    temp_service.save_evaluation(
        make_dummy_report(score_pct=70.0, traffic_light=TrafficLight.YELLOW),
        record_id="stat_y",
    )
    temp_service.save_evaluation(
        make_dummy_report(score_pct=40.0, traffic_light=TrafficLight.RED),
        record_id="stat_r",
    )

    stats: HistoryStats = temp_service.get_stats()
    assert stats.total_evaluations == 3
    # (90 + 70 + 40) / 3 = 66.7
    assert stats.average_score_pct == 66.7
    assert stats.count_green == 1
    assert stats.count_yellow == 1
    assert stats.count_red == 1
    assert stats.latest_timestamp is not None


def test_export_history_json(temp_service: HistoryService):
    """Verify exporting history records to valid JSON."""
    temp_service.save_evaluation(make_dummy_report(), record_id="exp_01")
    json_str = temp_service.export_history_json()
    data = json.loads(json_str)
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["id"] == "exp_01"
