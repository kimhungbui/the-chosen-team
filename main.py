import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from pipeline import evaluate_proposal, get_mock_evaluation_report, format_markdown_report
from utils.file_loader import load_document_file

def prompt_file_path(prompt_label: str, default_path: str) -> Path:
    """Interactively prompts user for a file path with default fallback and validation."""
    while True:
        try:
            val = input(f"{prompt_label} [{default_path}]: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nInput cancelled.")
            sys.exit(0)
        chosen = val if val else default_path
        p = Path(chosen).resolve()
        if p.exists() and p.is_file():
            return p
        print(f"   ⚠️ File not found at '{p}'. Please enter a valid file path.")

def main():
    parser = argparse.ArgumentParser(
        description="AI Proposal Scorer (Method 4: Multi-Agent + Guardrails)",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="Positional file arguments: [rfp_file] [proposal_file] [output_file]",
    )
    parser.add_argument(
        "-r", "--rfp",
        type=str,
        default=None,
        help="Path to client RFP document (.md, .txt, .pdf, .docx)",
    )
    parser.add_argument(
        "-p", "--proposal",
        type=str,
        default=None,
        help="Path to draft proposal document (.md, .txt, .pdf, .docx)",
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="eval_report.md",
        help="Output markdown file path to save the generated report",
    )
    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Interactively prompt for file paths in terminal",
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
    print("   Supported Input Formats: .md, .txt, .pdf, .docx")
    print("=" * 70)

    # Determine RFP and Proposal file paths
    pos_rfp = args.files[0] if len(args.files) >= 1 else None
    pos_proposal = args.files[1] if len(args.files) >= 2 else None
    pos_output = args.files[2] if len(args.files) >= 3 else None

    output_path = Path(pos_output or args.output)

    # Resolve RFP path
    rfp_arg = args.rfp or pos_rfp
    proposal_arg = args.proposal or pos_proposal

    if args.interactive or (not rfp_arg and not proposal_arg and sys.stdin.isatty()):
        print("\n📁 Interactive Document Selection:")
        rfp_path = prompt_file_path("  Enter path to Client RFP file", "sample_data/rfp_nordframe.md")
        proposal_path = prompt_file_path("  Enter path to Vendor Proposal file", "sample_data/response_1_weak.md")
    else:
        rfp_path = Path(rfp_arg or "sample_data/rfp_nordframe.md").resolve()
        proposal_path = Path(proposal_arg or "sample_data/response_1_weak.md").resolve()

        if not rfp_path.exists():
            print(f"❌ Error: RFP file not found at: {rfp_path}")
            sys.exit(1)
        if not proposal_path.exists():
            print(f"❌ Error: Proposal file not found at: {proposal_path}")
            sys.exit(1)

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

    # Ingest documents using universal file loader
    print(f"\n📂 Loading RFP Document:      {rfp_path}")
    rfp_content, rfp_meta = load_document_file(rfp_path)
    print(f"   ✓ Format: {rfp_meta['format']} | Size: {rfp_meta['size_bytes']:,} bytes | Lines: {rfp_meta['line_count']:,} | Chars: {rfp_meta['char_count']:,}")

    print(f"📄 Loading Proposal Document: {proposal_path}")
    proposal_content, prop_meta = load_document_file(proposal_path)
    print(f"   ✓ Format: {prop_meta['format']} | Size: {prop_meta['size_bytes']:,} bytes | Lines: {prop_meta['line_count']:,} | Chars: {prop_meta['char_count']:,}")

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
