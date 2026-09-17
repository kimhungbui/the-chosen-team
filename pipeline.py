import json
from typing import Optional
from models.schemas import RFPAnalysis, ComplianceMatrix, ProposalReviewReport
from agents.rfp_extractor import create_rfp_extractor_agent
from agents.compliance_auditor import create_compliance_auditor_agent
from agents.scorer_and_fixer import create_scorer_and_fixer_agent
from guardrails.verifier import (
    verify_citations_and_lines,
    enforce_mathematical_consistency,
    validate_actionable_fixes,
)

def evaluate_proposal(
    rfp_content: str,
    proposal_content: str,
    rfp_filename: str = "rfp.md",
    proposal_filename: str = "proposal.md",
    verbose: bool = True,
) -> ProposalReviewReport:
    """
    Executes Method 4 evaluation pipeline:
    1. Extract requirements & constraints from RFP.
    2. Cross-audit proposal against the extracted checklist.
    3. Score the 7 Appendix A criteria and draft concrete fixes.
    4. Deterministic Python guardrails: quote verification, line matching, and score math reconciliation.
    """
    if verbose:
        print("\n🔍 [Step 1/4] Extracting requirements and constraints from RFP...")

    rfp_extractor = create_rfp_extractor_agent()
    rfp_resp = rfp_extractor.run(
        f"Analyze this client RFP and extract all requirements, constraints, budget, timeline, and priorities:\n\n{rfp_content}"
    )
    rfp_analysis: RFPAnalysis = rfp_resp.content

    if verbose:
        print(f"   ✓ Extracted {len(rfp_analysis.requirements)} requirements/constraints.")
        print(f"   ✓ Detected Client Priority: {rfp_analysis.detected_client_priority}")
        print("\n📋 [Step 2/4] Cross-auditing proposal against RFP requirements checklist...")

    compliance_auditor = create_compliance_auditor_agent()
    audit_prompt = (
        f"### RFP Requirements Checklist:\n"
        f"{json.dumps([r.model_dump() for r in rfp_analysis.requirements], indent=2)}\n\n"
        f"### Vendor Proposal Draft:\n"
        f"{proposal_content}\n\n"
        f"Perform an exhaustive compliance audit of the proposal against each requirement in the checklist."
    )
    audit_resp = compliance_auditor.run(audit_prompt)
    compliance_matrix: ComplianceMatrix = audit_resp.content

    if verbose:
        met = sum(1 for i in compliance_matrix.items if i.status == "MET")
        missing = sum(1 for i in compliance_matrix.items if i.status == "MISSING")
        partial = sum(1 for i in compliance_matrix.items if i.status in ["PARTIALLY_MET", "DEFERRED"])
        contradicted = sum(1 for i in compliance_matrix.items if i.status == "CONTRADICTED")
        print(f"   ✓ Audit complete: {met} Met | {partial} Partial/Deferred | {missing} Missing | {contradicted} Contradicted")
        print("\n✍️  [Step 3/4] Generating rubric scores and drafting actionable fixes...")

    scorer_and_fixer = create_scorer_and_fixer_agent()
    scoring_prompt = (
        f"### Original RFP:\n{rfp_content}\n\n"
        f"### Proposal Draft:\n{proposal_content}\n\n"
        f"### Client Stated Priorities:\n{rfp_analysis.detected_client_priority}\n\n"
        f"### Compliance Audit Matrix:\n"
        f"{json.dumps([item.model_dump() for item in compliance_matrix.items], indent=2)}\n\n"
        f"Produce the full ProposalReviewReport scoring the 7 criteria and providing actionable fixes."
    )
    scoring_resp = scorer_and_fixer.run(scoring_prompt)
    report: ProposalReviewReport = scoring_resp.content

    if verbose:
        print("\n🛡️  [Step 4/4] Running Deterministic Python Guardrails...")

    # Python Guardrail Layer
    report = verify_citations_and_lines(
        report, rfp_content, proposal_content, rfp_filename, proposal_filename
    )
    report = enforce_mathematical_consistency(report, compliance_matrix)
    report.actionable_fixes = validate_actionable_fixes(report.actionable_fixes)

    if verbose:
        print(f"   ✓ Verified citations against source text.")
        print(f"   ✓ Enforced mathematical score consistency: Overall {report.overall_score}/5.0 ({report.readiness_verdict})")

    return report


def get_mock_evaluation_report(
    rfp_content: str,
    proposal_content: str,
    rfp_filename: str = "rfp.md",
    proposal_filename: str = "proposal.md",
) -> ProposalReviewReport:
    """
    Generates a deterministic benchmark report without requiring an API key.
    Useful for testing container builds, UI rendering, and guardrail logic offline.
    """
    from models.schemas import (
        CriterionScore,
        RequirementAudit,
        SuggestedFix,
        ProposalReviewReport,
        ComplianceMatrix,
    )

    compliance_items = [
        RequirementAudit(
            requirement_id="REQ-1",
            requirement_title="Web-based inventory dashboard across 6 warehouses",
            status="PARTIALLY_MET",
            rfp_quote="web-based dashboard showing real-time inventory levels across all 6 warehouses",
            proposal_quote="cloud-based dashboard that displays inventory data in real time",
            proposal_section="Our Approach",
            gap_analysis="Mentions cloud dashboard but does not confirm coverage across all 6 warehouse sites.",
        ),
        RequirementAudit(
            requirement_id="REQ-2",
            requirement_title="Automated low-stock alerts",
            status="MET",
            rfp_quote="Automated low-stock alerts sent to warehouse managers",
            proposal_quote="Notifications for low stock",
            proposal_section="Features",
            gap_analysis="Addressed in feature list, though lacking threshold configuration details.",
        ),
        RequirementAudit(
            requirement_id="REQ-3",
            requirement_title="Existing PostgreSQL database integration (no migration)",
            status="MISSING",
            rfp_quote="existing PostgreSQL inventory database — no migration to a new database",
            proposal_quote=None,
            proposal_section=None,
            gap_analysis="Crucial constraint missing. Proposal does not confirm PostgreSQL connection or rule out migration.",
        ),
        RequirementAudit(
            requirement_id="REQ-4",
            requirement_title="Role-based access (Warehouse vs HQ)",
            status="PARTIALLY_MET",
            rfp_quote="warehouse managers should only see their own site; HQ staff should see all sites",
            proposal_quote="Secure login for different users",
            proposal_section="Features",
            gap_analysis="Vague claim of secure login; omits specific warehouse vs HQ role separation.",
        ),
        RequirementAudit(
            requirement_id="REQ-5",
            requirement_title="Rollout & Onboarding plan across 6 sites",
            status="MISSING",
            rfp_quote="data migration / onboarding plan for rolling this out across all 6 sites",
            proposal_quote=None,
            proposal_section=None,
            gap_analysis="No rollout, onboarding, or migration strategy provided in proposal.",
        ),
        RequirementAudit(
            requirement_id="REQ-6",
            requirement_title="Support & Maintenance SLAs after go-live",
            status="MISSING",
            rfp_quote="Support & maintenance terms after go-live (response times, SLAs)",
            proposal_quote=None,
            proposal_section=None,
            gap_analysis="No post-launch support commitments, SLAs, or response time guarantees.",
        ),
        RequirementAudit(
            requirement_id="REQ-7",
            requirement_title="Assumptions, limitations, and risk disclosure",
            status="MISSING",
            rfp_quote="assumptions, limitations, or risks",
            proposal_quote=None,
            proposal_section=None,
            gap_analysis="Proposal completely omits risk disclosures and operational dependencies.",
        ),
    ]

    actionable_fixes = [
        SuggestedFix(
            category="MISSING_REQUIREMENT",
            title="Missing: PostgreSQL Integration Constraint",
            rfp_citation="existing PostgreSQL inventory database — no migration to a new database",
            proposal_citation="Our Approach",
            issue_description="The RFP requires connecting to the existing PostgreSQL database without migration. Proposal only mentions generic cloud architecture.",
            suggested_fix="The solution integrates directly with NordFrame's existing PostgreSQL inventory database via secure read/write connection pools. No database migration or schema disruption is required.",
        ),
        SuggestedFix(
            category="MISSING_REQUIREMENT",
            title="Missing: Support & Maintenance SLA Terms",
            rfp_citation="Support & maintenance terms after go-live (response times, SLAs)",
            proposal_citation="Why BrightPath",
            issue_description="RFP explicitly demands post-launch response times and SLAs; proposal ends with zero support terms.",
            suggested_fix="### Support & Maintenance Plan\n- **Coverage:** 24/7 incident monitoring with business-hours Tier-2 support.\n- **SLA Response Times:** Critical issues (P1) acknowledged within 1 hour; resolution target under 4 hours.\n- **Maintenance:** Quarterly non-disruptive security updates included in Year 1 support.",
        ),
        SuggestedFix(
            category="DEFERRED",
            title="Deferred: Pricing Breakdown within Budget",
            rfp_citation="Budget: €80,000–€120,000 total, including first year of support",
            proposal_citation="Pricing",
            issue_description="Pricing is completely deferred to 'further discussion' instead of framing within the €80k-€120k target.",
            suggested_fix="### Pricing Structure (Fixed Fee)\n- **Phase 1 (Pilot at single site):** €35,000\n- **Phase 2 (Rollout to remaining 5 sites):** €45,000\n- **Year 1 Support & SLA:** €15,000\n- **Total Investment:** €95,000 (fully within NordFrame's €80k–€120k budget).",
        ),
        SuggestedFix(
            category="DEFERRED",
            title="Deferred: Concrete Milestone Timeline",
            rfp_citation="Working pilot at one warehouse within 3 months; full rollout to all 6 sites within 6 months",
            proposal_citation="Timeline",
            issue_description="Proposal states vague 'timely manner' rather than committing to the 3-month and 6-month milestones.",
            suggested_fix="| Milestone | Target Date | Scope |\n|---|---|---|\n| M1: Pilot Go-Live | Month 3 | Central warehouse live with PostgreSQL integration |\n| M2: Multi-Site Rollout | Months 4-5 | Phased onboarding across remaining 5 regional sites |\n| M3: Full Handover & SLAs | Month 6 | Acceptance sign-off and 24/7 SLA activation |",
        ),
    ]

    criteria_scores = [
        CriterionScore(criterion="Problem Understanding", score=3.0, comment="States the general inventory visibility problem correctly, but lacks depth."),
        CriterionScore(criterion="Scope & Deliverables Clarity", score=2.0, comment="Feature list is generic bullet points; does not specify site-specific scope."),
        CriterionScore(criterion="Pricing Clarity", score=1.0, comment="Pricing entirely deferred to 'further discussion'."),
        CriterionScore(criterion="Timeline Clarity", score=1.0, comment="No dates or concrete milestones ('in a timely manner')."),
        CriterionScore(criterion="Completeness vs. RFP Requirements", score=1.6, comment="5 out of 7 core requirements missing or deferred."),
        CriterionScore(criterion="Tone & Persuasiveness", score=2.0, comment="Generic boilerplate, does not demonstrate deep logistics expertise."),
        CriterionScore(criterion="Risk/Assumptions Transparency", score=1.0, comment="Zero risks, assumptions, or dependencies disclosed."),
    ]

    report = ProposalReviewReport(
        proposal_title="Inventory Visibility Solution (Offline Test)",
        client_name="NordFrame Logistics GmbH",
        overall_score=1.7,
        readiness_verdict="MAJOR_REWORK_REQUIRED",
        verdict_summary="Proposal requires major revisions before submission. Critical constraints (PostgreSQL, SLAs, Timeline, Pricing) are omitted or deferred.",
        detected_client_priorities="Low operational risk, business continuity across 6 sites, and zero database migration disruption.",
        criteria_scores=criteria_scores,
        compliance_matrix=compliance_items,
        actionable_fixes=actionable_fixes,
    )

    # Run guardrails
    report = verify_citations_and_lines(report, rfp_content, proposal_content, rfp_filename, proposal_filename)
    report = enforce_mathematical_consistency(report, ComplianceMatrix(items=compliance_items, compliance_summary="Offline test"))
    return report


def format_markdown_report(report: ProposalReviewReport) -> str:
    """
    Renders the ProposalReviewReport into clean, presentation-ready Markdown
    matching the format of scoring_example.md.
    """
    verdict_emoji = {
        "READY_TO_SUBMIT": "🟢",
        "MINOR_REVISIONS_NEEDED": "🟡",
        "MAJOR_REWORK_REQUIRED": "🔴",
    }.get(report.readiness_verdict, "⚪")

    lines = []
    lines.append(f"# Proposal Evaluation Report: {report.proposal_title}")
    lines.append(f"**Client:** {report.client_name} | **Status:** {verdict_emoji} **{report.readiness_verdict.replace('_', ' ')}**")
    lines.append(f"**Overall Score:** {report.overall_score} / 5.0")
    lines.append(f"\n> **Detected Client Priority:** {report.detected_client_priorities}\n")
    lines.append(f"{report.verdict_summary}\n")

    lines.append("---\n")
    lines.append("## 1. Rubric Scores (7 Core Criteria)\n")
    lines.append("| Criterion | Score (1–5) | Comment |")
    lines.append("|---|---|---|")
    for score in report.criteria_scores:
        lines.append(f"| {score.criterion} | {score.score} | {score.comment} |")

    lines.append("\n---\n")
    lines.append("## 2. RFP Requirement Compliance Audit\n")
    lines.append("| Req ID | Requirement | Status | Gap / Analysis |")
    lines.append("|---|---|---|---|")
    for item in report.compliance_matrix:
        status_badge = {
            "MET": "✅ Met",
            "PARTIALLY_MET": "⚠️ Partial",
            "MISSING": "❌ Missing",
            "CONTRADICTED": "🚫 Contradicted",
            "DEFERRED": "⏳ Deferred",
        }.get(item.status, item.status)
        lines.append(f"| {item.requirement_id} | {item.requirement_title} | {status_badge} | {item.gap_analysis} |")

    lines.append("\n---\n")
    lines.append("## 3. Actionable Issues & Drafted Fixes (Copy-Pasteable)\n")
    for fix in report.actionable_fixes:
        category_icon = {
            "MISSING_REQUIREMENT": "❌",
            "VAGUE": "⚠️",
            "CONTRADICTION": "🚫",
            "DEFERRED": "⏳",
        }.get(fix.category, "🔹")
        lines.append(f"### {category_icon} {fix.title}")
        if fix.line_reference:
            lines.append(f"*Source References: {fix.line_reference}*")
        lines.append(f"- **RFP Requirement:** {fix.rfp_citation}")
        lines.append(f"- **Proposal Issue:** {fix.issue_description}")
        lines.append(f"\n**Suggested Fix (Ready to insert):**\n")
        lines.append(f"```markdown\n{fix.suggested_fix}\n```\n")

    return "\n".join(lines)
