from typing import List, Optional, Literal
from pydantic import BaseModel, Field

class RFPRequirement(BaseModel):
    id: str = Field(description="Unique ID e.g. REQ-1, REQ-2, CONSTRAINT-1")
    title: str = Field(description="Short title of the requirement")
    description: str = Field(description="Detailed requirement description from RFP")
    is_constraint: bool = Field(default=False, description="True if this is a negative constraint or strict boundary (e.g. no database migration)")
    priority: Literal["HIGH", "MEDIUM", "LOW"] = Field(default="HIGH", description="Priority based on client focus in RFP")
    exact_quote: str = Field(description="Verbatim quote snippet directly from the RFP text")

class RFPAnalysis(BaseModel):
    client_name: str = Field(description="Client company name")
    project_goal: str = Field(description="High level goal of the project")
    budget_range: str = Field(description="Budget specified in RFP, or 'Not specified'")
    timeline_requirement: str = Field(description="Timeline specified in RFP, or 'Not specified'")
    detected_client_priority: str = Field(description="Key client priority interpreted from RFP emphasis (e.g. low operational risk, continuity)")
    requirements: List[RFPRequirement] = Field(description="Extracted checklist of explicit requirements and constraints")

AuditStatus = Literal["MET", "PARTIALLY_MET", "MISSING", "CONTRADICTED", "DEFERRED"]

class RequirementAudit(BaseModel):
    requirement_id: str = Field(description="Matching RFPRequirement ID")
    requirement_title: str = Field(description="Title of the requirement")
    status: AuditStatus = Field(description="Evaluation status: MET, PARTIALLY_MET, MISSING, CONTRADICTED, or DEFERRED")
    rfp_quote: str = Field(description="Verbatim snippet from RFP")
    proposal_quote: Optional[str] = Field(default=None, description="Verbatim quote from proposal if addressed/partial/contradicted, or empty if missing")
    proposal_section: Optional[str] = Field(default=None, description="Section in the proposal where addressed or where it should appear")
    gap_analysis: str = Field(description="Clear explanation of how the proposal meets, fails, or contradicts this requirement")

class ComplianceMatrix(BaseModel):
    items: List[RequirementAudit] = Field(description="Detailed audit per RFP requirement")
    compliance_summary: str = Field(description="Summary of overall compliance findings")

class SuggestedFix(BaseModel):
    category: Literal["MISSING_REQUIREMENT", "VAGUE", "CONTRADICTION", "DEFERRED"] = Field(
        description="Category of the detected issue"
    )
    title: str = Field(description="Short descriptive issue title e.g. 'Missing: PostgreSQL integration constraint'")
    rfp_citation: str = Field(description="Exact RFP citation and requirement reference")
    proposal_citation: str = Field(description="Proposal section citation")
    issue_description: str = Field(description="Clear explanation of the flaw or gap")
    suggested_fix: str = Field(
        description="Concrete, copy-pasteable replacement text, drafted paragraph, milestone table, or SLA clause"
    )
    verified_in_source: bool = Field(default=False, description="Whether citations were verified verbatim against source documents")
    line_reference: Optional[str] = Field(default=None, description="Exact line or section reference resolved by verifier")

class CriterionScore(BaseModel):
    criterion: Literal[
        "Problem Understanding",
        "Scope & Deliverables Clarity",
        "Pricing Clarity",
        "Timeline Clarity",
        "Completeness vs. RFP Requirements",
        "Tone & Persuasiveness",
        "Risk/Assumptions Transparency"
    ] = Field(description="One of the 7 core scoring criteria from Appendix A")
    score: float = Field(description="Score between 1.0 and 5.0")
    comment: str = Field(description="Concise, substantive justification for this score")

class ProposalReviewReport(BaseModel):
    proposal_title: str = Field(description="Title of proposal")
    client_name: str = Field(description="Name of client")
    overall_score: float = Field(description="Aggregated overall score out of 5.0")
    readiness_verdict: Literal["READY_TO_SUBMIT", "MINOR_REVISIONS_NEEDED", "MAJOR_REWORK_REQUIRED"] = Field(
        description="Actionable verdict for sales team"
    )
    verdict_summary: str = Field(description="High-level assessment summary")
    detected_client_priorities: str = Field(description="Interpreted client focus from RFP")
    criteria_scores: List[CriterionScore] = Field(description="Scores across all 7 Appendix A criteria")
    compliance_matrix: List[RequirementAudit] = Field(description="RFP requirement compliance audit")
    actionable_fixes: List[SuggestedFix] = Field(description="Prioritized list of concrete fixes with drafted replacement text")
