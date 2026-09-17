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
    Configured with Pydantic structured output ExtractedRFP.
    """
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    selected_model = model_id or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    model = Gemini(id=selected_model, api_key=api_key)

    agent = Agent(
        name="RFP Requirement Extractor",
        model=model,
        description="Analyzes enterprise RFPs to extract structured requirements, business goals, and dynamic rubric weights.",
        output_model=ExtractedRFP,
        instructions=[
            "You are an expert RFP analyst at an IT consulting firm.",
            "Analyze the provided RFP text thoroughly.",
            "Extract the Client Name, Project Title, and a clear Executive Summary of the client's problem.",
            "Extract ALL explicit requirements (Technical, Scope, Timeline, Pricing, Compliance, Security) with unique IDs (REQ-01, REQ-02, etc.).",
            "Suggest optimal percentage rubric weights for evaluation based on the RFP priorities (sum of weights must equal 100).",
        ],
        markdown=True,
    )
    return agent
