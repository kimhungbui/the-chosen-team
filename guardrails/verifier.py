import re
from typing import Tuple, List, Optional
from models.schemas import ProposalReviewReport, ComplianceMatrix, SuggestedFix, RequirementAudit

def find_snippet_line_range(text: str, snippet: str) -> Optional[Tuple[int, int]]:
    """
    Finds the 1-based start and end line numbers of a snippet in the source text.
    Uses normalized whitespace for robust matching.
    """
    if not snippet or not snippet.strip():
        return None

    norm_snippet = " ".join(snippet.strip().split())
    lines = text.splitlines()

    # Direct line check
    for idx, line in enumerate(lines, 1):
        if norm_snippet.lower() in " ".join(line.split()).lower():
            return (idx, idx)

    # Multi-line sliding window check
    snippet_words = norm_snippet.lower().split()
    if not snippet_words:
        return None

    first_word = snippet_words[0]
    for start_idx, line in enumerate(lines):
        if first_word in line.lower():
            combined = ""
            for end_idx in range(start_idx, min(len(lines), start_idx + 8)):
                combined += " " + lines[end_idx]
                if norm_snippet.lower() in " ".join(combined.split()).lower():
                    return (start_idx + 1, end_idx + 1)

    # Substring search fallback
    pos = text.lower().find(snippet.strip().lower()[:min(30, len(snippet.strip()))])
    if pos != -1:
        start_line = text[:pos].count('\n') + 1
        return (start_line, start_line)

    return None

def verify_citations_and_lines(
    report: ProposalReviewReport,
    rfp_text: str,
    proposal_text: str,
    rfp_filename: str = "rfp.md",
    proposal_filename: str = "proposal.md"
) -> ProposalReviewReport:
    """
    Verifies that all citations and quotes exist in the source files,
    and attaches exact line numbers for UI traceability.
    """
    for fix in report.actionable_fixes:
        # Search in RFP
        rfp_lines = find_snippet_line_range(rfp_text, fix.rfp_citation)
        prop_lines = find_snippet_line_range(proposal_text, fix.proposal_citation)

        line_refs = []
        if rfp_lines:
            line_refs.append(f"{rfp_filename}:L{rfp_lines[0]}" + (f"-L{rfp_lines[1]}" if rfp_lines[1] > rfp_lines[0] else ""))
            fix.verified_in_source = True
        if prop_lines:
            line_refs.append(f"{proposal_filename}:L{prop_lines[0]}" + (f"-L{prop_lines[1]}" if prop_lines[1] > prop_lines[0] else ""))
            fix.verified_in_source = True

        if line_refs:
            fix.line_reference = " | ".join(line_refs)
        else:
            fix.line_reference = "Section match"

    # Also verify compliance matrix quotes
    for audit in report.compliance_matrix:
        rfp_lines = find_snippet_line_range(rfp_text, audit.rfp_quote)
        if rfp_lines:
            audit.gap_analysis += f" (RFP ref: L{rfp_lines[0]})"

    return report

def enforce_mathematical_consistency(
    report: ProposalReviewReport,
    compliance_matrix: ComplianceMatrix
) -> ProposalReviewReport:
    """
    Ensures that scores are mathematically sound and consistent with the compliance audit,
    preventing LLM hallucinated grades or score inflation.
    """
    total_reqs = len(compliance_matrix.items)
    if total_reqs > 0:
        met_count = sum(1 for item in compliance_matrix.items if item.status == "MET")
        partial_count = sum(1 for item in compliance_matrix.items if item.status in ["PARTIALLY_MET", "DEFERRED"])
        
        # Calculate objective completeness ratio
        compliance_ratio = (met_count + 0.5 * partial_count) / total_reqs
        objective_completeness = round(1.0 + (4.0 * compliance_ratio), 1)

        # Reconcile Completeness vs RFP Requirements score
        for score_item in report.criteria_scores:
            if score_item.criterion == "Completeness vs. RFP Requirements":
                # Cap or adjust if LLM deviated significantly from mathematical compliance
                if abs(score_item.score - objective_completeness) > 1.0:
                    score_item.score = objective_completeness
                    score_item.comment += f" [Adjusted to {met_count}/{total_reqs} requirements met]."

    # Re-calculate overall score deterministically as average of all criteria
    if report.criteria_scores:
        avg_score = round(sum(item.score for item in report.criteria_scores) / len(report.criteria_scores), 1)
        report.overall_score = avg_score

    # Determine readiness verdict objectively
    if report.overall_score < 2.5:
        report.readiness_verdict = "MAJOR_REWORK_REQUIRED"
    elif report.overall_score < 4.0:
        report.readiness_verdict = "MINOR_REVISIONS_NEEDED"
    else:
        report.readiness_verdict = "READY_TO_SUBMIT"

    return report

def validate_actionable_fixes(fixes: List[SuggestedFix]) -> List[SuggestedFix]:
    """
    Ensures fixes are concrete drafted text, cleans currency symbols,
    and sorts by deal-breaking severity (CRITICAL first).
    """
    severity_rank = {"CRITICAL": 0, "MAJOR": 1, "MINOR": 2}

    for fix in fixes:
        # Normalize any corrupted currency characters to proper UTF-8 Euro symbol
        fix.suggested_fix = fix.suggested_fix.replace(" ", "€").replace("––", "–")
        fix.issue_description = fix.issue_description.replace(" ", "€").replace("––", "–")

        text = fix.suggested_fix.strip()
        # If fix is too short or reads like generic instruction, enrich with placeholder template
        if len(text.split()) < 10 or text.lower().startswith("you should improve"):
            fix.suggested_fix = (
                f"**Draft Clause to insert:**\n\n"
                f"> \"{text}\"\n\n"
                f"*Note: Ensure concrete figures and parameters are confirmed.*"
            )

    # Sort so CRITICAL constraints and deferred pricing appear first
    fixes.sort(key=lambda f: severity_rank.get(f.severity, 1))
    return fixes
