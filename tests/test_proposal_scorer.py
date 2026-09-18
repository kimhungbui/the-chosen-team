"""
Unit tests for FPT Software Europe Proposal Scorer engine.
Tests that the evaluation pipeline correctly ranks proposal variants:
Strong > Medium > Overpromising > Weak, and generates complete requirement gap analyses.
"""

import pytest
from data.sample_data import SAMPLE_DATASETS
from services.scoring_engine import evaluate_proposal, recalculate_report_scores, DEFAULT_WEIGHTS
from schema.proposal_models import TrafficLight, RequirementCoverageStatus


def test_sample_proposals_ranking():
    rfp_text = SAMPLE_DATASETS["rfp"]["content"]
    rfp_title = SAMPLE_DATASETS["rfp"]["title"]

    proposals = SAMPLE_DATASETS["proposals"]

    report_strong = evaluate_proposal(
        rfp_text=rfp_text,
        proposal_text=proposals["response_3_strong"]["content"],
        proposal_title=proposals["response_3_strong"]["title"],
        rfp_title=rfp_title,
        force_fallback=True,
    )

    report_medium = evaluate_proposal(
        rfp_text=rfp_text,
        proposal_text=proposals["response_2_medium"]["content"],
        proposal_title=proposals["response_2_medium"]["title"],
        rfp_title=rfp_title,
        force_fallback=True,
    )

    report_overpromise = evaluate_proposal(
        rfp_text=rfp_text,
        proposal_text=proposals["response_4_overpromise"]["content"],
        proposal_title=proposals["response_4_overpromise"]["title"],
        rfp_title=rfp_title,
        force_fallback=True,
    )

    report_weak = evaluate_proposal(
        rfp_text=rfp_text,
        proposal_text=proposals["response_1_weak"]["content"],
        proposal_title=proposals["response_1_weak"]["title"],
        rfp_title=rfp_title,
        force_fallback=True,
    )

    # Assert expected score ordering
    assert report_strong.overall_score_pct > report_medium.overall_score_pct, "Strong score must exceed Medium score"
    assert report_medium.overall_score_pct > report_weak.overall_score_pct, "Medium score must exceed Weak score"

    # Assert traffic lights
    assert report_strong.overall_traffic_light == TrafficLight.GREEN, "Strong proposal should be GREEN"
    assert report_medium.overall_traffic_light == TrafficLight.YELLOW, "Medium proposal should be YELLOW"
    assert report_weak.overall_traffic_light == TrafficLight.RED, "Weak proposal should be RED"

    # Assert rubric score counts
    assert len(report_strong.rubric_scores) == 7, "Must evaluate all 7 Appendix A criteria"

    # Assert gap detection for weak proposal
    assert len(report_weak.requirement_gaps) > 0, "Weak proposal must have identified requirement gaps"
    assert len(report_weak.requirement_gaps[0].actionable_rewrite) > 20, "Must provide actionable rewrite suggestions"


def test_custom_rubric_weights():
    rfp_text = SAMPLE_DATASETS["rfp"]["content"]
    proposal_text = SAMPLE_DATASETS["proposals"]["response_3_strong"]["content"]

    custom_weights = {
        "problem_understanding": 10.0,
        "scope_deliverables_clarity": 20.0,
        "pricing_clarity": 30.0,  # Heavily weighted pricing
        "timeline_clarity": 10.0,
        "completeness_vs_rfp": 20.0,
        "tone_persuasiveness": 5.0,
        "risk_transparency": 5.0,
    }

    report = evaluate_proposal(
        rfp_text=rfp_text,
        proposal_text=proposal_text,
        custom_weights=custom_weights,
        force_fallback=True,
    )

    assert report.overall_score_pct > 80.0
    pricing_crit = next(c for c in report.rubric_scores if c.criterion_id == "pricing_clarity")
    assert pricing_crit.weight == 30.0


def test_why_high_why_low_factors_and_citations():
    rfp_text = SAMPLE_DATASETS["rfp"]["content"]
    strong_prop = SAMPLE_DATASETS["proposals"]["response_3_strong"]["content"]
    weak_prop = SAMPLE_DATASETS["proposals"]["response_1_weak"]["content"]

    report_strong = evaluate_proposal(rfp_text=rfp_text, proposal_text=strong_prop, force_fallback=True)
    report_weak = evaluate_proposal(rfp_text=rfp_text, proposal_text=weak_prop, force_fallback=True)

    # Verify detected client priorities (Level 3)
    assert len(report_strong.detected_client_priorities) > 10, "Should detect client strategic priorities"

    # Verify strong proposal has why-high factors
    strong_pricing = next(c for c in report_strong.rubric_scores if c.criterion_id == "pricing_clarity")
    assert strong_pricing.score_1_to_5 >= 4.5
    assert len(strong_pricing.score_factors_high) > 0, "Strong pricing must explain why score is high"
    assert len(strong_pricing.citations) > 0, "Must include supporting citations"

    # Verify weak proposal has why-low factors
    weak_pricing = next(c for c in report_weak.rubric_scores if c.criterion_id == "pricing_clarity")
    assert weak_pricing.score_1_to_5 <= 1.5
    assert len(weak_pricing.score_factors_low) > 0, "Weak pricing must explain why score was penalized"
    assert len(weak_pricing.citations) > 0, "Must include citations pointing out omission/deferral"

    # Verify actionable placement anchor & priority level on requirement gaps
    first_gap = report_weak.requirement_gaps[0]
    assert len(first_gap.placement_anchor) > 0, "Requirement gap must specify exact placement anchor in proposal"
    assert first_gap.priority_level in ["CRITICAL", "HIGH", "MEDIUM"], "Must assign valid priority level"


def test_arbitrary_domain_evaluation():
    custom_rfp = """
    # Request for Proposal: Clinical Trial Telehealth Platform
    **Client:** St. Jude Medical Group
    **Requirements:**
    1. HIPAA-compliant video consultations with end-to-end encryption.
    2. Zero database migration — integrate directly with our existing HL7 FHIR server.
    3. Maximum budget of $150,000 including Year 1 maintenance.
    4. Pilot launch in 3 months.
    """

    custom_proposal = """
    # Proposal: CareLink Telehealth Solution
    We will build a cloud-based dashboard for video consultations.
    Pricing will be discussed later depending on requirements.
    Timeline will be determined after kickoff.
    """

    report = evaluate_proposal(
        rfp_text=custom_rfp,
        proposal_text=custom_proposal,
        proposal_title="CareLink Proposal",
        rfp_title="St. Jude Telehealth RFP",
        force_fallback=True,
    )

    assert report.overall_score_pct < 50.0, "Vague/deferred proposal should score low"
    assert report.overall_traffic_light == TrafficLight.RED
    assert len(report.rubric_scores) == 7
    assert len(report.requirement_gaps) > 0
    assert report.detected_client_priorities != ""
    assert "NordFrame" not in str(report), "Custom RFP must not leak hardcoded NordFrame text"
    assert "PostgreSQL" not in str(report), "Custom RFP must not leak hardcoded PostgreSQL text"


def test_dynamic_rfp_healthcare_dataset():
    with open("sample_data/healthcare_telehealth/rfp.md") as f:
        rfp_text = f.read()
    with open("sample_data/healthcare_telehealth/response_3_strong.md") as f:
        strong_text = f.read()
    with open("sample_data/healthcare_telehealth/response_4_overpromise.md") as f:
        over_text = f.read()

    rep_strong = evaluate_proposal(rfp_text, strong_text, force_fallback=True)
    rep_over = evaluate_proposal(rfp_text, over_text, force_fallback=True)

    # Assert no hardcoded NordFrame leakage
    assert "NordFrame" not in str(rep_strong)
    assert "NordFrame" not in str(rep_over)
    assert "€102,000" not in str(rep_strong)

    # Assert correct domain client
    assert "MediCare Systems" in rep_strong.detected_client_priorities or "MediCare" in rep_strong.executive_summary

    # Strong must score higher than Overpromising
    assert rep_strong.overall_score_pct > rep_over.overall_score_pct
    assert rep_strong.overall_traffic_light == TrafficLight.GREEN


def test_error_handling_and_no_silent_fallback(monkeypatch):
    # Test that missing key raises ValueError when fallback is disallowed
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    with pytest.raises(ValueError) as exc_info:
        evaluate_proposal("rfp content", "proposal content", allow_fallback_on_error=False)
    assert "Gemini API Key missing" in str(exc_info.value)

    # Test that error is recorded on report when fallback is allowed
    monkeypatch.setenv("GEMINI_API_KEY", "INVALID_MOCK_KEY")
    rep = evaluate_proposal("rfp content", "proposal content", allow_fallback_on_error=True)
    assert rep.engine_mode == "rule_engine"
    assert rep.llm_error is not None


def test_company_name_mismatch_sets_score_to_zero():
    # Cross-dataset mismatch: NordFrame RFP + MediCare Proposal
    with open("sample_data/rfp_nordframe.md") as f:
        rfp_nordframe = f.read()
    with open("sample_data/healthcare_telehealth/response_3_strong.md") as f:
        prop_medicare = f.read()

    report_mismatch = evaluate_proposal(
        rfp_text=rfp_nordframe,
        proposal_text=prop_medicare,
        force_fallback=True,
    )

    # Must be 0% and RED
    assert report_mismatch.overall_score_pct == 0.0, "Mismatched company name must result in 0% score"
    assert report_mismatch.overall_traffic_light == TrafficLight.RED
    assert "FATAL DISQUALIFICATION" in report_mismatch.executive_summary
    assert "Target Company Mismatch" in report_mismatch.executive_summary

    # All rubric scores should have 0.0 weighted score
    for rubric in report_mismatch.rubric_scores:
        assert rubric.weighted_score == 0.0
        assert rubric.traffic_light == TrafficLight.RED

    # Must have a critical disqualification gap
    disq_gap = next((g for g in report_mismatch.requirement_gaps if g.requirement_id == "REQ-DISQUALIFY"), None)
    assert disq_gap is not None
    assert disq_gap.priority_level == "CRITICAL"


def test_custom_company_name_mismatch_and_match():
    rfp = """
    # Request for Proposal
    **Client:** Tesla Motors Inc.
    ## Requirements
    1. Factory telemetry dashboard.
    """

    prop_wrong = """
    # Proposal for Ford Motor Company
    **Prepared for:** Ford Motor Company
    We propose telemetry dashboards for Ford factories.
    """

    prop_right = """
    # Proposal for Tesla Motors Inc.
    **Prepared for:** Tesla Motors Inc.
    We propose telemetry dashboards for Tesla factories.
    """

    rep_wrong = evaluate_proposal(rfp, prop_wrong, force_fallback=True)
    assert rep_wrong.overall_score_pct == 0.0
    assert rep_wrong.overall_traffic_light == TrafficLight.RED

    rep_right = evaluate_proposal(rfp, prop_right, force_fallback=True)
    assert rep_right.overall_score_pct > 0.0


def test_ambiguous_customer_requirements_detection_and_mitigation():
    with open("sample_data/retail_ambiguous/rfp.md") as f:
        rfp_text = f.read()
    with open("sample_data/retail_ambiguous/response_3_strong.md") as f:
        strong_prop = f.read()
    with open("sample_data/retail_ambiguous/response_1_weak.md") as f:
        weak_prop = f.read()

    rep_strong = evaluate_proposal(rfp_text=rfp_text, proposal_text=strong_prop, force_fallback=True)
    rep_weak = evaluate_proposal(rfp_text=rfp_text, proposal_text=weak_prop, force_fallback=True)

    # 1. Ambiguous requirements must be detected in the vague customer RFP
    assert len(rep_strong.ambiguous_requirements) >= 3, "Must detect ambiguous requirements in RFP"
    assert len(rep_weak.ambiguous_requirements) >= 3

    # 2. Each ambiguous requirement must have clarification question and protective assumption
    for amb in rep_strong.ambiguous_requirements:
        assert len(amb.clarification_question) > 10, "Must provide pre-bid RFI clarification question"
        assert len(amb.recommended_assumption) > 10, "Must provide protective baseline assumption"

    # 3. Strong proposal mitigates ambiguities with baseline assumptions
    handled_count = sum(1 for a in rep_strong.ambiguous_requirements if a.proposal_handling == "HANDLED_WITH_ASSUMPTIONS")
    assert handled_count >= 2, "Strong proposal must handle ambiguities with explicit assumptions"

    # 4. Weak proposal naively repeats vague buzzwords
    vague_count = sum(1 for a in rep_weak.ambiguous_requirements if a.proposal_handling == "REPEATED_VAGUELY")
    assert vague_count >= 2, "Weak proposal should be caught repeating vague customer terms"

    # 5. Strong proposal must score substantially higher than weak proposal
    assert rep_strong.overall_score_pct > rep_weak.overall_score_pct
    assert rep_strong.overall_traffic_light == TrafficLight.GREEN
    assert rep_weak.overall_traffic_light in [TrafficLight.RED, TrafficLight.YELLOW]


def test_recalculate_report_scores_instant_and_accurate():
    rfp_text = SAMPLE_DATASETS["rfp"]["content"]
    strong_prop = SAMPLE_DATASETS["proposals"]["response_3_strong"]["content"]

    # Generate initial report with default weights
    report = evaluate_proposal(rfp_text=rfp_text, proposal_text=strong_prop, force_fallback=True)
    initial_score = report.overall_score_pct
    initial_pricing = next(c for c in report.rubric_scores if c.criterion_id == "pricing_clarity")
    assert initial_pricing.weight == 15.0

    # Apply new custom weights: bump pricing to 40%, reduce others
    new_weights = {
        "problem_understanding": 10.0,
        "scope_deliverables_clarity": 10.0,
        "pricing_clarity": 40.0,
        "timeline_clarity": 10.0,
        "completeness_vs_rfp": 10.0,
        "tone_persuasiveness": 10.0,
        "risk_transparency": 10.0,
    }

    updated_report = recalculate_report_scores(report, new_weights)

    # Verify that the report itself is returned updated
    assert updated_report is report
    updated_pricing = next(c for c in updated_report.rubric_scores if c.criterion_id == "pricing_clarity")
    assert updated_pricing.weight == 40.0
    expected_pricing_weighted = round((updated_pricing.score_1_to_5 / 5.0) * 40.0, 2)
    assert updated_pricing.weighted_score == expected_pricing_weighted

    # Verify overall score matches sum of weighted scores
    expected_total = round(sum(c.weighted_score for c in updated_report.rubric_scores), 1)
    assert updated_report.overall_score_pct == expected_total

    # Verify resetting weights restores the original score without re-evaluating
    reset_report = recalculate_report_scores(report, DEFAULT_WEIGHTS)
    assert reset_report.overall_score_pct == initial_score


def test_recalculate_preserves_company_mismatch_disqualification():
    rfp = """
    # Request for Proposal
    **Client:** Tesla Motors Inc.
    ## Requirements
    1. Factory telemetry dashboard.
    """
    prop_wrong = """
    # Proposal for Ford Motor Company
    **Prepared for:** Ford Motor Company
    We propose telemetry dashboards for Ford factories.
    """

    rep_wrong = evaluate_proposal(rfp, prop_wrong, force_fallback=True)
    assert rep_wrong.overall_score_pct == 0.0
    assert rep_wrong.overall_traffic_light == TrafficLight.RED

    # Recalculating with any weights must keep 0.0% disqualified score
    new_weights = {k: 100.0 / 7.0 for k in DEFAULT_WEIGHTS}
    recalculated = recalculate_report_scores(rep_wrong, new_weights)
    assert recalculated.overall_score_pct == 0.0
    assert recalculated.overall_traffic_light == TrafficLight.RED






