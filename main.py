import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from pipeline import evaluate_proposal, get_mock_evaluation_report, format_markdown_report

def main():
    parser = argparse.ArgumentParser(description="AI Proposal Scorer (Method 4: Multi-Agent + Guardrails)")
    parser.add_argument(
        "--rfp",
        type=str,
        default="sample_data/rfp_nordframe.md",
        help="Path to the client RFP document (Markdown)",
    )
    parser.add_argument(
        "--proposal",
        type=str,
        default="sample_data/response_1_weak.md",
        help="Path to the draft proposal document (Markdown)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="eval_report.md",
        help="Output markdown file path to save the generated report",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Run offline mock test mode without calling Gemini API",
    )
    args = parser.parse_args()

    print("=" * 70)
    print("🏆 PROPOSAL SCORER & REVIEWER (SiviHack 2026 - Track 1)")
    print("   Architecture: Method 4 (Agno Multi-Agent + Deterministic Guardrails)")
    print("=" * 70)

    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    use_mock = args.mock

    if not gemini_key and not use_mock:
        print("\n💡 NOTICE: No GEMINI_API_KEY found in environment or .env file.")
        print("   Automatically switching to 🧪 OFFLINE MOCK MODE to test container,")
        print("   schemas, guardrails, line resolution, and report generation.")
        print("   (To use live LLM agents, add GEMINI_API_KEY to your .env file)\n")
        use_mock = True
    elif use_mock:
        print("\n🧪 OFFLINE MOCK MODE explicitly enabled (No API key needed).")

    rfp_path = Path(args.rfp)
    proposal_path = Path(args.proposal)

    if not rfp_path.exists():
        print(f"❌ Error: RFP file not found at: {rfp_path}")
        sys.exit(1)
    if not proposal_path.exists():
        print(f"❌ Error: Proposal file not found at: {proposal_path}")
        sys.exit(1)

    print(f"\n📂 Ingesting RFP:      {rfp_path}")
    print(f"📄 Ingesting Proposal: {proposal_path}")

    rfp_content = rfp_path.read_text(encoding="utf-8")
    proposal_content = proposal_path.read_text(encoding="utf-8")

    try:
        if use_mock:
            report = get_mock_evaluation_report(
                rfp_content=rfp_content,
                proposal_content=proposal_content,
                rfp_filename=rfp_path.name,
                proposal_filename=proposal_path.name,
            )
        else:
            report = evaluate_proposal(
                rfp_content=rfp_content,
                proposal_content=proposal_content,
                rfp_filename=rfp_path.name,
                proposal_filename=proposal_path.name,
                verbose=True,
            )

        # Format and save report
        md_report = format_markdown_report(report)
        output_path = Path(args.output)
        output_path.write_text(md_report, encoding="utf-8")

        print("\n" + "=" * 70)
        print(f"✅ Evaluation Complete! Report successfully written to: {output_path}")
        print(f"📊 Overall Score: {report.overall_score} / 5.0  [{report.readiness_verdict}]")
        print("=" * 70)
        print("\n" + md_report)

    except Exception as e:
        print(f"\n❌ Pipeline execution failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
