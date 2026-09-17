from agno.agent import Agent
from agents.assistant import get_model
from models.schemas import RFPAnalysis

def create_rfp_extractor_agent() -> Agent:
    """
    Creates an Agno Agent dedicated to parsing the RFP into a structured checklist
    of requirements, constraints, commercial targets, and client priorities.
    """
    return Agent(
        name="RFP Requirements Extractor",
        model=get_model("gemini-2.5-flash"),
        output_schema=RFPAnalysis,
        instructions=[
            "You are an expert enterprise RFP analyst.",
            "Carefully analyze the provided Request for Proposal (RFP).",
            "Extract all explicit deliverables, functional requirements, technical constraints, budget, timeline, and SLA expectations.",
            "Identify strict negative constraints (e.g., 'no migration to new database', 'no downtime') and mark is_constraint=True.",
            "Detect the underlying client priorities and business concerns (e.g. low operational risk, business continuity vs cutting-edge innovation).",
            "For every requirement, capture an exact verbatim snippet directly from the RFP text in exact_quote.",
        ],
    )
