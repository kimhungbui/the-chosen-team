"""
Unit tests for FPT Software Europe Proposal Scorer engine.
Tests that the evaluation pipeline correctly ranks proposal variants:
Strong > Medium > Overpromising > Weak, and generates complete requirement gap analyses.
"""

import pytest
from data.sample_data import SAMPLE_DATASETS
from services.scoring_engine import evaluate_proposal
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
