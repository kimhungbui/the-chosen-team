"""
Synthetic Benchmark Dataset Generator for Proposal Scorer.
Uses Agno Multi-Agent framework with Google Gemini to generate
end-to-end evaluation bundles (1 Client RFP + 4 Proposal Variants: Strong, Medium, Weak, Overpromise).
"""

import os
import sys
import argparse
from typing import Dict
from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.google import Gemini
from pydantic import BaseModel, Field

load_dotenv()


class BenchmarkDatasetBundle(BaseModel):
    industry_domain: str = Field(..., description="Industry domain e.g. Healthcare, Fintech")
    client_name: str = Field(..., description="Fictional client name")
    project_title: str = Field(..., description="Project title")
    rfp_markdown: str = Field(..., description="Complete markdown content of client RFP")
    response_1_weak_markdown: str = Field(..., description="Complete markdown content of Weak proposal variant")
    response_2_medium_markdown: str = Field(..., description="Complete markdown content of Medium proposal variant")
    response_3_strong_markdown: str = Field(..., description="Complete markdown content of Strong proposal variant")
    response_4_overpromise_markdown: str = Field(..., description="Complete markdown content of Overpromising proposal variant")


def create_dataset_generator_agent() -> Agent:
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if api_key:
        os.environ["GOOGLE_API_KEY"] = api_key
        os.environ["GEMINI_API_KEY"] = api_key

    model_id = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
    model = Gemini(id=model_id, api_key=api_key)

    agent = Agent(
        name="Dataset Generator",
        model=model,
        description="Generates realistic enterprise RFP and 4-variant proposal benchmark datasets.",
        output_schema=BenchmarkDatasetBundle,
        instructions=[
            "You are an Enterprise Procurement Director & Bid Management Expert.",
            "Your mission is to generate a realistic, rigorous evaluation benchmark dataset consisting of 1 Client RFP and 4 Proposal Variants.",
            "THE CLIENT RFP MUST CONTAIN:",
            "1. # Request for Proposal — <Project Title>",
            "2. Client details & Industry context",
            "3. Clear Background & Problem Statement",
            "4. Exactly 6 to 7 numbered explicit requirements",
            "5. At least 1 CRITICAL NEGATIVE CONSTRAINT (e.g. 'Must integrate with existing on-premise system X — no database migration or cloud replacement allowed')",
            "6. Stated Budget Range (e.g. €100,000–€150,000 total, including 1st year support)",
            "7. Concrete Timeline expectations (e.g. working pilot within 3 months, full rollout within 6 months)",
            "",
            "THE 4 PROPOSAL VARIANTS MUST BE:",
            "- RESPONSE 1 (WEAK): Generic sales boilerplate, surface-level problem understanding, defers pricing ('to be discussed based on detailed requirements'), uncommitted timeline ('in a timely manner'), zero risks or SLAs.",
            "- RESPONSE 2 (MEDIUM): Solid functional understanding, good technical features, but pricing is an uncommitted broad estimate range with firm quote deferred to discovery, timeline has no milestone dates, support/risks vague.",
            "- RESPONSE 3 (STRONG): Fully satisfies RFP. Itemized fixed pricing table strictly within budget cap, detailed phased rollout table meeting pilot & go-live deadlines, explicitly confirms and honors the negative constraint, dedicated Risks & Assumptions chapter.",
            "- RESPONSE 4 (OVERPROMISING): Scope creep (adds unrequested predictive AI/analytics), directly CONTRADICTS the negative constraint (e.g. proposes migrating to their proprietary cloud platform), promises unrealistic hyper-fast delivery (e.g. 6 weeks).",
        ],
        markdown=True,
    )
    return agent


def generate_and_save_dataset(topic: str, output_dir: str):
    print(f"🚀 Generating benchmark dataset for topic: '{topic}'...")
    agent = create_dataset_generator_agent()

    prompt = f"""
Generate a complete benchmark evaluation pack for:
Topic: {topic}

Ensure:
- RFP has a hard negative constraint, realistic budget cap, and timeline.
- Weak proposal scores ~20-30%.
- Medium proposal scores ~50-65%.
- Strong proposal scores ~90-98%.
- Overpromising proposal scores ~30-45% due to scope creep, unrealistic timeline, and constraint violation.
"""

    response = agent.run(prompt)
    bundle: BenchmarkDatasetBundle = response.content

    os.makedirs(output_dir, exist_ok=True)

    files_to_save = {
        "rfp.md": bundle.rfp_markdown,
        "response_1_weak.md": bundle.response_1_weak_markdown,
        "response_2_medium.md": bundle.response_2_medium_markdown,
        "response_3_strong.md": bundle.response_3_strong_markdown,
        "response_4_overpromise.md": bundle.response_4_overpromise_markdown,
    }

    print(f"\n📂 Saving dataset files to: {output_dir}")
    for filename, content in files_to_save.items():
        filepath = os.path.join(output_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content.strip() + "\n")
        print(f"   ✅ Saved {filename} ({len(content)} chars)")

    print(f"\n🎉 Successfully created benchmark dataset for '{bundle.project_title}' ({bundle.client_name})!")
    return output_dir


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic RFP & proposal evaluation benchmarks.")
    parser.add_argument("--topic", type=str, default="Healthcare Clinical Telehealth & EHR Integration Platform", help="Domain/industry topic for the RFP")
    parser.add_argument("--outdir", type=str, default=None, help="Target folder to save generated markdown files")

    args = parser.parse_args()

    topic_slug = args.topic.lower().replace(" ", "_").replace("&", "and")[:30]
    outdir = args.outdir or os.path.join("sample_data", topic_slug)

    generate_and_save_dataset(args.topic, outdir)


if __name__ == "__main__":
    main()
