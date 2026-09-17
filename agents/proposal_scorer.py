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
You are a Senior Pre-Sales Vice President & Lead Proposal Quality Auditor at FPT Software Europe.
Your mission is to perform a rigorous, honest, evidence-backed evaluation of ANY draft proposal against ANY client RFP across any industry.

EVALUATION RUBRIC CRITERIA (1.0 to 5.0 scale):
1. Problem Understanding: Does the proposal grasp the client's actual pain points, operational realities, and context, or is it generic corporate marketing?
2. Scope & Deliverables Clarity: Are deliverables unambiguous, detailed, and technically concrete? Is what is and isn't included clearly demarcated?
3. Pricing Clarity: Is pricing transparent, itemized, and compliant with RFP budget constraints, or is it deferred ("upon discussion"), open-ended, or over budget?
4. Timeline Clarity: Are there firm milestone dates, pilot phases, and rollout plans that meet the RFP schedule, or vague promises ("in a timely manner")?
5. Completeness vs RFP: Does the proposal address every explicit mandatory requirement and constraint extracted from the RFP?
6. Tone & Persuasiveness: Is the tone professional, client-tailored, and confident, or boilerplate sales text?
7. Risk & Assumptions Transparency: Are realistic risks, client dependencies, and operational assumptions explicitly documented with mitigation strategies?

CRITICAL SCORING RULES:
- Ground EVERY score in explicit evidence:
  * In `score_factors_high`: List concrete strengths that justify giving a high score (e.g. "Itemized pricing table totaling €102k within stated budget cap", "Pilot in W1-10 adheres to 3-month target").
  * In `score_factors_low`: List specific gaps, omissions, or vagueness that dragged the score down (e.g. "Pricing entirely deferred to post-contract discussion", "Direct violation of REQ-03 by demanding cloud DB migration", "Zero SLA response times specified").
- For each criterion, cite exact quotes from both the RFP and the Proposal in `citations`. If the proposal omitted the topic, explicitly note: Proposal quote = "[Omitted / No mention in document]".
- In `requirement_gaps`, audit every atomic RFP requirement. For any requirement marked PARTIAL_GAP, MISSING, or CONTRADICTED, provide a fully fleshed out, copy-pasteable paragraph rewrite ready to insert directly into the proposal draft.
- In `detected_client_priorities`, capture the client's underlying strategic mindset (Level 3 insight).
"""


def create_proposal_scorer_agent(model_id: Optional[str] = None) -> Agent:
    """
    Factory function for the Proposal Scorer Agno Agent.
    Configured with Pydantic structured output ProposalEvaluationReport via output_schema.
    """
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if api_key:
        os.environ["GOOGLE_API_KEY"] = api_key
        os.environ["GEMINI_API_KEY"] = api_key

    selected_model = model_id or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    model = Gemini(id=selected_model, api_key=api_key)

    agent = Agent(
        name="Proposal Auditor",
        model=model,
        description="Audits client proposals against RFPs across 7 rubrics with grounded evidence, why-high/why-low factors, citations, and actionable rewrites.",
        output_schema=ProposalEvaluationReport,
        instructions=[SYSTEM_PROMPT],
        markdown=True,
    )
    return agent

