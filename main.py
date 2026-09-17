"""
Main Entry Point for Proposal Scorer — FPT Software Europe (SiviHack 2026).
"""

import os
import sys
from dotenv import load_dotenv
from data.sample_data import SAMPLE_DATASETS
from services.scoring_engine import evaluate_proposal

load_dotenv()


def main():
    print("=" * 70)
    print("🎯 Proposal Scorer — FPT Software Europe (SiviHack 2026)")
    print("=" * 70)

    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if gemini_key:
        print("🔑 Gemini API Key detected. Engine ready for Agno LLM Multi-Agent mode.")
    else:
        print("⚡ Operating in Deterministic High-Fidelity Rule Engine Mode.")

    print("\n--- Running Evaluation Benchmark on Appendix B Sample Proposal Variants ---")
    rfp_text = SAMPLE_DATASETS["rfp"]["content"]
    rfp_title = SAMPLE_DATASETS["rfp"]["title"]

    for key, item in SAMPLE_DATASETS["proposals"].items():
        report = evaluate_proposal(
            rfp_text=rfp_text,
            proposal_text=item["content"],
            proposal_title=item["title"],
            rfp_title=rfp_title,
        )

        traffic_badge = "🟢" if report.overall_traffic_light == "GREEN" else ("🟡" if report.overall_traffic_light == "YELLOW" else "🔴")
        print(f"\n[{traffic_badge} {report.overall_traffic_light}] {item['title']}")
        print(f"   Overall Score: {report.overall_score_pct}%")
        print(f"   Verdict: {report.executive_summary[:120]}...")
        print(f"   Requirement Gaps Identified: {len(report.requirement_gaps)}")

    print("\n" + "=" * 70)
    print("🚀 To launch the interactive Streamlit Web Dashboard, run:")
    print("   .venv/bin/streamlit run app.py")
    print("=" * 70)


if __name__ == "__main__":
    main()
