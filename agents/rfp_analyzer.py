"""
RFP Analyzer Agent built using Agno framework with Google Gemini.
Extracts structured requirements, business goals, constraints, and dynamic rubric weightings from RFP text.
"""

import os
from typing import Optional
from agno.agent import Agent
from agno.models.google import Gemini
from schema.proposal_models import ExtractedRFP


def create_rfp_analyzer_agent(model_id: Optional[str] = None) -> Agent:
    """
    Factory function for the RFP Analyzer Agno Agent.
    Configured with Pydantic structured output ExtractedRFP via output_schema.
    """
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if api_key:
        os.environ["GOOGLE_API_KEY"] = api_key
        os.environ["GEMINI_API_KEY"] = api_key

    selected_model = model_id or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    model = Gemini(id=selected_model, api_key=api_key)

    agent = Agent(
        name="RFP Requirement Extractor",
        model=model,
        description="Analyzes enterprise RFPs across any industry to extract atomic requirements, commercial constraints, and implicit client priorities.",
        output_schema=ExtractedRFP,
        instructions=[
            "You are an expert Enterprise RFP Analyst & Pre-Sales Solutions Architect.",
            "Analyze the provided RFP text thoroughly. The RFP can belong to ANY industry (logistics, healthcare, finance, software, etc.).",
            "Extract the Client Name, Project Title, and an Executive Summary of the client's business context and problem statement.",
            "Identify and extract DETECTED CLIENT PRIORITIES: Analyze what the client truly values most beneath the surface (e.g. operational continuity, minimal disruption, data sovereignty, strict budget predictability vs cutting-edge innovation).",
            "Extract all COMMERCIAL CONSTRAINTS: Budget ranges/caps, firm pilot and go-live milestone dates, and hard negative constraints (e.g. 'no database migration', 'on-premise only', 'no vendor lock-in').",
            "Extract ALL atomic, verifiable requirements with unique IDs (REQ-01, REQ-02, etc.), assigning appropriate Category (Technical, Scope, Timeline, Pricing, Compliance, Support) and Priority (MANDATORY, HIGH, MEDIUM).",
            "Recommend optimal percentage weights for the 7 standard rubric criteria based on this client's unique priorities (must sum to 100).",
        ],
        markdown=True,
    )
    return agent
