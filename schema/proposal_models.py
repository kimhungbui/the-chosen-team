"""
Pydantic Data Models for FPT Software Europe Proposal Scorer System.
Defines schemas for RFP extraction, 7-criterion rubric scoring,
citations, requirement gap analysis, and comprehensive evaluation reports.
"""

from enum import Enum
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class TrafficLight(str, Enum):
    GREEN = "GREEN"    # Strong match / high quality (4.0 - 5.0)
    YELLOW = "YELLOW"  # Moderate match / needs refinement (2.5 - 3.9)
    RED = "RED"        # Critical gap / weak / risky (1.0 - 2.4)


class RequirementCoverageStatus(str, Enum):
    FULFILLED = "FULFILLED"
    PARTIAL_GAP = "PARTIAL_GAP"
    MISSING = "MISSING"
    CONTRADICTED = "CONTRADICTED"


class RFPRequirement(BaseModel):
    id: str = Field(..., description="Unique ID for requirement, e.g., REQ-01")
    title: str = Field(..., description="Short title of the requirement")
    category: str = Field(..., description="Category: Technical, Scope, Timeline, Pricing, Compliance, Security")
    description_snippet: str = Field(..., description="Exact requirement snippet or summary from RFP")
    priority: str = Field("MANDATORY", description="MANDATORY, HIGH, MEDIUM, LOW")
    section_ref: str = Field("Section 1", description="Section in RFP where this appears")


class ExtractedRFP(BaseModel):
    client_name: str = Field(..., description="Client name, e.g., NordFrame Logistics")
    project_title: str = Field(..., description="Project name, e.g., Enterprise Cloud Migration & Modernization")
    executive_summary: str = Field(..., description="High-level overview of RFP goals and problem context")
    detected_client_priorities: str = Field(
        "", 
        description="Implicit client priority/philosophy extracted from RFP (e.g. continuity and minimal disruption over cutting-edge novelty)"
    )
    commercial_constraints: List[str] = Field(
        default_factory=list,
        description="Budget caps, hard milestone deadlines, and explicit technical exclusions (e.g. no DB migration)"
    )
    requirements: List[RFPRequirement] = Field(default_factory=list, description="Extracted individual client requirements")
    recommended_weights: Dict[str, float] = Field(
        default_factory=lambda: {
            "problem_understanding": 15.0,
            "scope_deliverables_clarity": 20.0,
            "pricing_clarity": 15.0,
            "timeline_clarity": 15.0,
            "completeness_vs_rfp": 20.0,
            "tone_persuasiveness": 5.0,
            "risk_transparency": 10.0,
        },
        description="Suggested rubric weightings (sum to 100)"
    )


class Citation(BaseModel):
    rfp_section: str = Field("", description="RFP section name or number")
    rfp_quote: str = Field("", description="Relevant quote or snippet from RFP")
    proposal_section: str = Field("", description="Proposal section name or number")
    proposal_quote: str = Field("", description="Relevant quote or snippet from proposal")


class CriterionScore(BaseModel):
    criterion_id: str = Field(..., description="Key identifier e.g. problem_understanding")
    criterion_name: str = Field(..., description="Display name e.g. Problem Understanding")
    score_1_to_5: float = Field(..., description="Numerical score from 1.0 to 5.0")
    weight: float = Field(15.0, description="Percentage weight assigned to this criterion")
    weighted_score: float = Field(0.0, description="Calculated score (score_1_to_5 * weight / 5)")
    traffic_light: TrafficLight = Field(TrafficLight.GREEN, description="Status rating")
    rationale: str = Field(..., description="Detailed explanation of why this score was given (why high or why low)")
    score_factors_high: List[str] = Field(
        default_factory=list,
        description="Explicit strengths justifying why the score is high (e.g. specific deliverables, transparent budget match)"
    )
    score_factors_low: List[str] = Field(
        default_factory=list,
        description="Explicit weaknesses/gaps justifying why the score is low (e.g. deferred pricing, vague timeline, omitted SLAs)"
    )
    citations: List[Citation] = Field(default_factory=list, description="Supporting document citations")
    suggested_fixes: List[str] = Field(default_factory=list, description="Quick actionable feedback items")


class RequirementGap(BaseModel):
    requirement_id: str = Field(..., description="Requirement ID from RFP e.g. REQ-03")
    requirement_title: str = Field(..., description="Requirement title")
    status: RequirementCoverageStatus = Field(RequirementCoverageStatus.MISSING)
    rfp_snippet: str = Field("", description="What the RFP requested")
    proposal_snippet: str = Field("", description="What the proposal currently says (or empty if missing)")
    issue_description: str = Field(..., description="Explanation of missing or weak coverage")
    placement_anchor: str = Field(
        "",
        description="Exact location in the proposal where this fix should be placed (e.g., 'Insert as Section 3.2 after System Architecture' or 'Add as a standalone Appendix: Risks')"
    )
    priority_level: str = Field(
        "HIGH",
        description="Remediation urgency: CRITICAL (causes RFP disqualification), HIGH (drastically lowers score), MEDIUM (improves polish)"
    )
    actionable_rewrite: str = Field(..., description="Concrete, copy-pasteable paragraph rewrite or new section text")


class AmbiguousRequirement(BaseModel):
    requirement_id: str = Field(..., description="ID or reference of ambiguous requirement e.g. REQ-02 or SEC-3")
    requirement_title: str = Field("Ambiguous Requirement", description="Short title of the requirement")
    rfp_snippet: str = Field(..., description="Vague or underspecified snippet from customer RFP")
    ambiguity_reason: str = Field(..., description="Why this requirement is not clear (e.g. lacks metrics, missing tech stack, undefined volume/SLA)")
    proposal_handling: str = Field(
        "UNADDRESSED", 
        description="How proposal handled it: HANDLED_WITH_ASSUMPTIONS, REPEATED_VAGUELY, or UNADDRESSED"
    )
    clarification_question: str = Field(..., description="Specific pre-bid RFI clarification question to ask the customer")
    recommended_assumption: str = Field(..., description="Protective scoping assumption to insert into proposal to prevent scope creep")


class ProposalEvaluationReport(BaseModel):
    proposal_title: str = Field(..., description="Name or file of draft proposal")
    rfp_title: str = Field(..., description="Name of matching RFP")
    detected_client_priorities: str = Field(
        "", 
        description="Interpreted client strategic priorities and operational sensitivity from RFP"
    )
    overall_score_pct: float = Field(..., description="Overall weighted percentage (0.0 to 100.0%)")
    overall_traffic_light: TrafficLight = Field(TrafficLight.GREEN)
    executive_summary: str = Field(..., description="Executive verdict summarizing readiness and key issues")
    rubric_scores: List[CriterionScore] = Field(default_factory=list, description="Scores across all 7 rubrics")
    requirement_gaps: List[RequirementGap] = Field(default_factory=list, description="Detailed RFP gap analysis")
    ambiguous_requirements: List[AmbiguousRequirement] = Field(
        default_factory=list,
        description="Audit of unclear/ambiguous customer requirements, RFI clarification questions, and defensive assumptions"
    )
    top_strengths: List[str] = Field(default_factory=list, description="Highlighted strong points")
    top_risks_and_remediations: List[str] = Field(default_factory=list, description="Critical risks needing attention before submission")
    rfp_metrics: Dict[str, Any] = Field(default_factory=dict, description="Format, page/slide count, and word metrics for RFP")
    proposal_metrics: Dict[str, Any] = Field(default_factory=dict, description="Format, page/slide count, and word metrics for proposal")
    engine_mode: str = Field("agno_llm", description="Evaluation engine used (agno_llm or rule_engine)")
    engine_notice: str = Field("", description="Notice or warnings from engine execution")
    llm_error: Optional[str] = Field(None, description="Error message if LLM agent evaluation failed")
    llm_error_traceback: Optional[str] = Field(None, description="Full traceback of LLM failure")


