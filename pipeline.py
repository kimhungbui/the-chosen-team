import json
import time
from typing import Optional, Type, TypeVar
from models.schemas import RFPAnalysis, ComplianceMatrix, ProposalReviewReport
from agents.rfp_extractor import create_rfp_extractor_agent
from agents.compliance_auditor import create_compliance_auditor_agent
from agents.scorer_and_fixer import create_scorer_and_fixer_agent
from guardrails.verifier import (
    verify_citations_and_lines,
    enforce_mathematical_consistency,
    validate_actionable_fixes,
)

T = TypeVar("T")

def _run_agent_with_retry(
    agent_factory,
    prompt: str,
    expected_type: Type[T],
    agent_name: str = "Agent",
    max_retries: int = 4,
    base_delay: float = 3.0,
) -> T:
    """
    Executes an Agno agent call with exponential backoff retry on transient
    API errors such as Gemini 503 high demand spikes.
    """
    for attempt in range(1, max_retries + 1):
        try:
            agent = agent_factory()
            resp = agent.run(prompt)
            content = resp.content
            
            if isinstance(content, expected_type):
                return content
            elif isinstance(content, str):
                if any(err_code in content for err_code in ["503", "UNAVAILABLE", "ResourceExhausted", "429"]):
                    raise RuntimeError(f"Gemini API transient rate/demand error: {content[:200]}")
                # Try parsing JSON if schema validation was returned as raw JSON text
                clean = content.strip()
                if clean.startswith("```json"):
                    clean = clean[7:]
                if clean.startswith("```"):
                    clean = clean[3:]
                if clean.endswith("```"):
                    clean = clean[:-3]
                return expected_type.model_validate_json(clean.strip())
            elif isinstance(content, dict):
                return expected_type.model_validate(content)
            else:
                raise RuntimeError(f"Unexpected agent output type: {type(content)}")
        except Exception as e:
            if attempt < max_retries:
                wait_time = base_delay * (1.5 ** (attempt - 1))
                print(f"   ⚠️  [{agent_name}] Attempt {attempt} failed ({str(e)[:120]}). Retrying in {wait_time:.1f}s...")
                time.sleep(wait_time)
            else:
                print(f"   ❌ [{agent_name}] All {max_retries} attempts failed: {e}")
                raise e

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
        print("\n" + "=" * 75)
        print("🔍 [STEP 1/4: RFP REQUIREMENTS & CONSTRAINTS EXTRACTION]")
        print("   Agent 1 (RFPExtractorAgent) reading RFP with Gemini 3.5 Flash...")
        print("=" * 75)

    rfp_analysis: RFPAnalysis = _run_agent_with_retry(
        agent_factory=create_rfp_extractor_agent,
        prompt=f"Analyze this client RFP and extract all requirements, constraints, budget, timeline, and priorities:\n\n{rfp_content}",
        expected_type=RFPAnalysis,
        agent_name="RFPExtractorAgent",
    )

    if verbose:
        print(f"\n📌 Client Name:        {rfp_analysis.client_name}")
        print(f"🎯 Project Goal:       {rfp_analysis.project_goal}")
        print(f"💰 Commercial Budget:  {rfp_analysis.budget_range}")
        print(f"⏱️  Delivery Target:   {rfp_analysis.timeline_requirement}")
        print(f"🧠 Detected Priority:  {rfp_analysis.detected_client_priority}")
        print(f"\n📋 Checklist of Recalled Requirements & Constraints ({len(rfp_analysis.requirements)} total):")
        for idx, req in enumerate(rfp_analysis.requirements, 1):
            constraint_tag = " [🚨 STRICT CONSTRAINT]" if req.is_constraint else ""
            print(f"   [{idx}] {req.id}: {req.title}{constraint_tag} (Priority: {req.priority})")
            print(f"       Verbatim RFP Quote: \"{req.exact_quote}\"")

        print("\n" + "=" * 75)
        print("📋 [STEP 2/4: COMPLIANCE AUDIT & EVIDENCE RECALL]")
        print("   Agent 2 (ComplianceAuditorAgent) cross-referencing proposal against checklist...")
        print("=" * 75)

    audit_prompt = (
        f"### RFP Requirements Checklist:\n"
        f"{json.dumps([r.model_dump() for r in rfp_analysis.requirements], indent=2)}\n\n"
        f"### Vendor Proposal Draft:\n"
        f"{proposal_content}\n\n"
        f"Perform an exhaustive compliance audit of the proposal against each requirement in the checklist."
    )
    compliance_matrix: ComplianceMatrix = _run_agent_with_retry(
        agent_factory=create_compliance_auditor_agent,
        prompt=audit_prompt,
        expected_type=ComplianceMatrix,
        agent_name="ComplianceAuditorAgent",
    )

    if verbose:
        print("\n📊 Cross-Audit Evidence Recalled from Proposal:")
        for item in compliance_matrix.items:
            icon = {
                "MET": "✅ MET",
                "PARTIALLY_MET": "⚠️  PARTIAL",
                "MISSING": "❌ MISSING",
                "CONTRADICTED": "🚫 CONTRADICTED",
                "DEFERRED": "⏳ DEFERRED"
            }.get(item.status, item.status)
            print(f"\n   • {item.requirement_id} ({item.requirement_title}): {icon}")
            if item.proposal_quote:
                print(f"     Recalled Proposal Quote: \"{item.proposal_quote}\" (Section: {item.proposal_section})")
            else:
                print("     Recalled Proposal Quote: [NO EVIDENCE FOUND - REQUIREMENT OMITTED]")
            print(f"     Audit Gap Analysis: {item.gap_analysis}")

        met = sum(1 for i in compliance_matrix.items if i.status == "MET")
        missing = sum(1 for i in compliance_matrix.items if i.status == "MISSING")
        partial = sum(1 for i in compliance_matrix.items if i.status in ["PARTIALLY_MET", "DEFERRED"])
        contradicted = sum(1 for i in compliance_matrix.items if i.status == "CONTRADICTED")
        print(f"\n   📈 Audit Summary: {met} Met | {partial} Partial/Deferred | {missing} Missing | {contradicted} Contradicted")

        print("\n" + "=" * 75)
        print("✍️  [STEP 3/4: 7-CRITERIA SCORING & ACTIONABLE FIX DRAFTING]")
        print("   Agent 3 (ScorerAndFixerAgent) calibrating rubrics & drafting clauses...")
        print("=" * 75)

    scoring_prompt = (
        f"### Original RFP:\n{rfp_content}\n\n"
        f"### Proposal Draft:\n{proposal_content}\n\n"
        f"### Client Stated Priorities:\n{rfp_analysis.detected_client_priority}\n\n"
        f"### Compliance Audit Matrix:\n"
        f"{json.dumps([item.model_dump() for item in compliance_matrix.items], indent=2)}\n\n"
        f"Produce the full ProposalReviewReport scoring the 7 criteria and providing actionable fixes."
    )
    report: ProposalReviewReport = _run_agent_with_retry(
        agent_factory=create_scorer_and_fixer_agent,
        prompt=scoring_prompt,
        expected_type=ProposalReviewReport,
        agent_name="ScorerAndFixerAgent",
    )

    if verbose:
        print("\n🏆 Rubric Scores Derived:")
        for score in report.criteria_scores:
            print(f"   • {score.criterion}: {score.score}/5.0 — {score.comment}")

        print(f"\n✍️  Drafted Actionable Fixes ({len(report.actionable_fixes)} total):")
        for idx, fix in enumerate(report.actionable_fixes, 1):
            sev_badge = getattr(fix, "severity", "MAJOR")
            print(f"\n   [{idx}] [{sev_badge}] {fix.title}")
            print(f"       RFP Ref: \"{fix.rfp_citation}\" | Proposal Sec: {fix.proposal_citation}")
            print(f"       Issue: {fix.issue_description}")
            print("       Suggested Replacement:")
            for line in fix.suggested_fix.splitlines()[:5]:
                print(f"         {line}")
            if len(fix.suggested_fix.splitlines()) > 5:
                print("         [... table / clause continues ...]")

        print("\n" + "=" * 75)
        print("🛡️  [STEP 4/4: DETERMINISTIC PYTHON GUARDRAIL VERIFICATION]")
        print("=" * 75)

    # Python Guardrail Layer
    report = verify_citations_and_lines(
        report, rfp_content, proposal_content, rfp_filename, proposal_filename
    )
    report = enforce_mathematical_consistency(report, compliance_matrix)
    report.actionable_fixes = validate_actionable_fixes(report.actionable_fixes)

    if verbose:
        print("   ✓ Verbatim Quote Verification & Line Resolution:")
        for fix in report.actionable_fixes:
            print(f"     - {fix.title}: {fix.line_reference} (Verified in source: {fix.verified_in_source})")
        print(f"   ✓ Mathematical Consistency Enforced: Overall {report.overall_score}/5.0 ({report.readiness_verdict})")

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
