import unittest
from pathlib import Path
from guardrails.verifier import (
    find_snippet_line_range,
    verify_citations_and_lines,
    enforce_mathematical_consistency,
    validate_actionable_fixes,
)
from pipeline import get_mock_evaluation_report
from models.schemas import RequirementAudit, ComplianceMatrix, SuggestedFix, ProposalReviewReport, CriterionScore

class TestGuardrailsOffline(unittest.TestCase):
    def setUp(self):
        self.rfp_path = Path("sample_data/rfp_nordframe.md")
        self.proposal_path = Path("sample_data/response_1_weak.md")
        self.rfp_text = self.rfp_path.read_text(encoding="utf-8")
        self.proposal_text = self.proposal_path.read_text(encoding="utf-8")

    def test_find_snippet_line_range(self):
        # Test finding line range in RFP
        snippet = "existing PostgreSQL inventory database"
        res = find_snippet_line_range(self.rfp_text, snippet)
        self.assertIsNotNone(res)
        self.assertEqual(res[0], 17)

    def test_end_to_end_mock_evaluation(self):
        # Run mock evaluation (no API key needed)
        report = get_mock_evaluation_report(
            rfp_content=self.rfp_text,
            proposal_content=self.proposal_text,
            rfp_filename=self.rfp_path.name,
            proposal_filename=self.proposal_path.name,
        )

        # Check basic properties
        self.assertIsInstance(report, ProposalReviewReport)
        self.assertEqual(len(report.criteria_scores), 7)
        self.assertTrue(len(report.actionable_fixes) >= 4)

        # Ensure citations were resolved to line numbers
        postgres_fix = next(f for f in report.actionable_fixes if "PostgreSQL" in f.title)
        self.assertTrue(postgres_fix.verified_in_source)
        self.assertIn("rfp_nordframe.md:L17", postgres_fix.line_reference)

        # Check mathematical score enforcement
        self.assertLessEqual(report.overall_score, 2.5)
        self.assertEqual(report.readiness_verdict, "MAJOR_REWORK_REQUIRED")

    def test_mathematical_consistency_guardrail(self):
        # Create a mock report with an artificially inflated score
        audit_items = [
            RequirementAudit(
                requirement_id="REQ-1",
                requirement_title="Req 1",
                status="MISSING",
                rfp_quote="q1",
                gap_analysis="missing",
            ),
            RequirementAudit(
                requirement_id="REQ-2",
                requirement_title="Req 2",
                status="MISSING",
                rfp_quote="q2",
                gap_analysis="missing",
            ),
        ]
        matrix = ComplianceMatrix(items=audit_items, compliance_summary="All missing")
        scores = [
            CriterionScore(criterion="Completeness vs. RFP Requirements", score=4.5, comment="Inflated"),
            CriterionScore(criterion="Problem Understanding", score=2.0, comment="Test"),
        ]
        report = ProposalReviewReport(
            proposal_title="Test",
            client_name="Test",
            overall_score=4.25,
            readiness_verdict="READY_TO_SUBMIT",
            verdict_summary="Test",
            detected_client_priorities="None",
            criteria_scores=scores,
            compliance_matrix=audit_items,
            actionable_fixes=[],
        )

        # Apply guardrail
        enforce_mathematical_consistency(report, matrix)

        # Completeness should have been corrected from 4.5 down to 1.0 (since 0/2 met)
        completeness = next(s for s in report.criteria_scores if s.criterion == "Completeness vs. RFP Requirements")
        self.assertEqual(completeness.score, 1.0)
        self.assertEqual(report.readiness_verdict, "MAJOR_REWORK_REQUIRED")

if __name__ == "__main__":
    unittest.main()
