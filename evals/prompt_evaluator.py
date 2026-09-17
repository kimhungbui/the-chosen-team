import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, List

# Ensure project root in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from models.schemas import ProposalReviewReport
from pipeline import evaluate_proposal, get_mock_evaluation_report
from guardrails.verifier import find_snippet_line_range

# Ground Truth Targets from sample_data/scoring_example.md & challenge specs
GROUND_TRUTH = {
    "response_1_weak.md": {
        "expected_score": 1.7,
        "expected_verdict": "MAJOR_REWORK_REQUIRED",
        "must_catch_missing": ["PostgreSQL", "SLA", "Pricing", "Timeline", "Rollout"],
        "must_penalize_tone": True,
    },
    "response_2_medium.md": {
        "expected_score": 2.9,
        "expected_verdict": "MINOR_REVISIONS_NEEDED",
        "must_catch_missing": ["SLA", "Risk"],
        "must_flag_vague": ["Pricing", "Timeline"],
    },
    "response_3_strong.md": {
        "expected_score": 4.8,
        "expected_verdict": "READY_TO_SUBMIT",
        "must_catch_missing": [],
        "min_completeness_score": 4.5,
    },
    "response_4_overpromise.md": {
        "expected_score": 1.9,
        "expected_verdict": "MAJOR_REWORK_REQUIRED",
        "must_flag_contradiction": "migration",
        "must_flag_unrealistic_timeline": True,
    }
}

META_ADVICE_TRIGGERS = [
    "you should consider",
    "please improve",
    "it is recommended to improve",
    "make sure to clarify",
    "needs to be more clear",
    "improve clarity",
]

def evaluate_report_quality(
    report: ProposalReviewReport,
    variant_filename: str,
    rfp_text: str,
    proposal_text: str
) -> Dict[str, Any]:
    """
    Computes quantitative evaluation metrics for a single proposal evaluation report.
    """
    target = GROUND_TRUTH.get(variant_filename, {})
    
    # 1. Score Calibration Error (|predicted - target|)
    expected_score = target.get("expected_score", 3.0)
    score_error = abs(report.overall_score - expected_score)
    score_accuracy = max(0.0, 1.0 - (score_error / 4.0)) # 1.0 = perfect match

    # 2. Verdict Match
    verdict_match = (report.readiness_verdict == target.get("expected_verdict"))

    # 3. Constraint & Negative Requirement Recall
    constraint_detected = True
    if "must_flag_contradiction" in target:
        keyword = target["must_flag_contradiction"].lower()
        # Look for contradiction or violation flag in fixes or compliance matrix
        has_flag = any(
            (item.status == "CONTRADICTED" or keyword in item.gap_analysis.lower())
            for item in report.compliance_matrix
        ) or any(keyword in fix.issue_description.lower() for fix in report.actionable_fixes)
        if not has_flag:
            constraint_detected = False

    # 4. Citation Grounding Precision (verbatim search)
    citations_total = 0
    citations_grounded = 0
    for fix in report.actionable_fixes:
        citations_total += 1
        has_rfp = find_snippet_line_range(rfp_text, fix.rfp_citation) is not None
        has_prop = find_snippet_line_range(proposal_text, fix.proposal_citation) is not None
        if has_rfp or has_prop or fix.verified_in_source:
            citations_grounded += 1

    grounding_rate = (citations_grounded / citations_total) if citations_total > 0 else 1.0

    # 5. Fix Actionability Ratio
    # Real fixes must be > 20 words and NOT contain meta-advice phrasing
    actionable_count = 0
    fixes_total = len(report.actionable_fixes)
    for fix in report.actionable_fixes:
        text = fix.suggested_fix.lower().strip()
        word_count = len(text.split())
        has_meta = any(trigger in text for trigger in META_ADVICE_TRIGGERS)
        if word_count >= 20 and not has_meta:
            actionable_count += 1

    actionability_rate = (actionable_count / fixes_total) if fixes_total > 0 else 1.0

    # Composite Score (0 - 100)
    composite_score = round(
        (score_accuracy * 30.0) +
        ((1.0 if verdict_match else 0.0) * 20.0) +
        ((1.0 if constraint_detected else 0.0) * 20.0) +
        (grounding_rate * 15.0) +
        (actionability_rate * 15.0),
        1
    )

    return {
        "variant": variant_filename,
        "predicted_score": report.overall_score,
        "expected_score": expected_score,
        "score_error": round(score_error, 2),
        "verdict_match": verdict_match,
        "constraint_recall": 1.0 if constraint_detected else 0.0,
        "grounding_rate": round(grounding_rate, 2),
        "actionability_rate": round(actionability_rate, 2),
        "composite_score": composite_score,
    }


def run_prompt_evaluation_loop(use_mock: bool = False) -> Dict[str, Any]:
    """
    Runs the automated prompt evaluation loop across all 4 sample datasets.
    """
    sample_dir = PROJECT_ROOT / "sample_data"
    rfp_path = sample_dir / "rfp_nordframe.md"
    rfp_text = rfp_path.read_text(encoding="utf-8")

    variants = [
        "response_1_weak.md",
        "response_2_medium.md",
        "response_3_strong.md",
        "response_4_overpromise.md",
    ]

    print("=" * 75)
    print("🔬 AUTOMATED PROMPT EVALUATION LOOP (SiviHack 2026)")
    print(f"   Mode: {'🧪 Offline Mock Mode' if use_mock else '🤖 Live Gemini Model Evaluation'}")
    print("=" * 75)

    results = []
    for variant in variants:
        prop_path = sample_dir / variant
        prop_text = prop_path.read_text(encoding="utf-8")

        print(f"\nEvaluating: {variant} ...")

        if use_mock:
            from web.server import get_variant_mock_report
            report = get_variant_mock_report(rfp_text, prop_text, variant)
        else:
            report = evaluate_proposal(
                rfp_content=rfp_text,
                proposal_content=prop_text,
                rfp_filename=rfp_path.name,
                proposal_filename=prop_path.name,
                verbose=False
            )

        metrics = evaluate_report_quality(report, variant, rfp_text, prop_text)
        results.append(metrics)

        print(f"  Score: {metrics['predicted_score']}/5.0 (Target: {metrics['expected_score']}) | Error: {metrics['score_error']}")
        print(f"  Verdict Match: {'✅' if metrics['verdict_match'] else '❌'} | Constraint Caught: {'✅' if metrics['constraint_recall'] == 1.0 else '❌'}")
        print(f"  Grounding: {int(metrics['grounding_rate']*100)}% | Actionability: {int(metrics['actionability_rate']*100)}% | Quality Score: {metrics['composite_score']}/100")

    # Aggregate Metrics
    avg_composite = round(sum(r["composite_score"] for r in results) / len(results), 1)
    avg_score_error = round(sum(r["score_error"] for r in results) / len(results), 2)
    avg_grounding = round(sum(r["grounding_rate"] for r in results) / len(results), 2)
    avg_actionability = round(sum(r["actionability_rate"] for r in results) / len(results), 2)
    total_verdicts_matched = sum(1 for r in results if r["verdict_match"])
    constraints_caught = sum(1 for r in results if r["constraint_recall"] == 1.0)

    summary = {
        "avg_composite_score": avg_composite,
        "avg_score_calibration_error": avg_score_error,
        "avg_grounding_rate": avg_grounding,
        "avg_actionability_rate": avg_actionability,
        "verdict_accuracy": f"{total_verdicts_matched}/{len(variants)}",
        "constraint_recall": f"{constraints_caught}/{len(variants)}",
        "detailed_results": results
    }

    print("\n" + "=" * 75)
    print(f"🏆 OVERALL PROMPT SUITE QUALITY SCORE: {avg_composite} / 100")
    print(f"   • Score Calibration MAE:  {avg_score_error} points")
    print(f"   • Citation Grounding:     {int(avg_grounding * 100)}%")
    print(f"   • Fix Actionability:      {int(avg_actionability * 100)}%")
    print(f"   • Verdict Accuracy:       {summary['verdict_accuracy']}")
    print(f"   • Constraint Recall:      {summary['constraint_recall']}")
    print("=" * 75)

    return summary

if __name__ == "__main__":
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    use_mock_mode = (len(sys.argv) > 1 and sys.argv[1] == "--mock") or (not gemini_key)
    run_prompt_evaluation_loop(use_mock=use_mock_mode)
