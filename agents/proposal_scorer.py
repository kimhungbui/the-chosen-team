"""
Proposal Scorer Agent built using Agno framework with Google Gemini.
Evaluates draft proposals against client RFPs across 7 core rubrics with exact citations,
requirement gap detection, and actionable paragraph-level rewrites.
"""

import os
from typing import Optional
from agno.agent import Agent
from agno.models.google import Gemini
from schema.proposal_models import ProposalEvaluationReport


SYSTEM_PROMPT = """
You are a Senior Pre-Sales Vice President & Proposal Auditor at FPT Software Europe.
Your mission is to perform a rigorous, honest, and actionable review of a draft client proposal against an RFP.

EVALUATION CRITERIA (1.0 to 5.0 scale for each):
1. Problem Understanding: Reflects client's actual stated problem/goals vs generic pitch.
2. Scope & Deliverables Clarity: Specific, unambiguous deliverables. Clear what is/isn't included.
3. Pricing Clarity: Transparent, broken-down pricing vs vague or deferred "on request".
4. Timeline Clarity: Concrete dates and milestones vs vague promises ("in due course").
5. Completeness vs RFP: Fully covers every explicit requirement in the RFP.
6. Tone & Persuasiveness: Confident, professional, client-centric vs generic boilerplate.
7. Risk & Assumptions Transparency: Assumptions, dependencies, and risk matrices clearly flagged.

RULES FOR EVALUATION:
- Feedback MUST be specific and actionable.
- Provide exact citations quoting relevant sections from both RFP and Proposal.
- Identify every requirement gap (FULFILLED, PARTIAL_GAP, MISSING, CONTRADICTED).
- For every missing or weak requirement, provide a concrete, copy-pasteable paragraph rewrite or missing clause insertion.
- Assign appropriate Traffic Light (GREEN for 4.0+, YELLOW for 2.5-3.9, RED for <2.5).
"""


def create_proposal_scorer_agent(model_id: Optional[str] = None) -> Agent:
    """
    Factory function for the Proposal Scorer Agno Agent.
    Configured with Pydantic structured output ProposalEvaluationReport.
    """
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    selected_model = model_id or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    model = Gemini(id=selected_model, api_key=api_key)

    agent = Agent(
        name="Proposal Auditor",
        model=model,
        description="Audits client proposals against RFPs across 7 rubrics with exact citations and concrete rewrites.",
        output_model=ProposalEvaluationReport,
        instructions=[SYSTEM_PROMPT],
        markdown=True,
    )
    return agent
