import os
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
        model=get_model(os.getenv("GEMINI_MODEL", "gemini-3.5-flash")),
        output_schema=RFPAnalysis,
        instructions=[
            "You are a seasoned enterprise RFP procurement analyst and contracts officer.",
            "Your objective is to dissect the client's Request for Proposal (RFP) into a comprehensive, unambiguous requirement taxonomy.",
            "",
            "CORE EXTRACTION RULES:",
            "1. TAXONOMY CLASSIFICATION: Classify each item into one of 5 categories:",
            "   - FUNCTIONAL: Core feature requests (e.g. real-time dashboard, automated alerts).",
            "   - ARCHITECTURAL CONSTRAINT: Strict negative boundaries the vendor MUST NOT violate (e.g. 'no database migration', 'must connect to existing PostgreSQL'). Mark is_constraint=True!",
            "   - COMMERCIAL BOUND: Budget limits, cost expectations, or pricing terms (e.g. €80,000–€120,000 total).",
            "   - DELIVERY MILESTONES: Strict timeline deadlines (e.g. 3-month pilot, 6-month full rollout).",
            "   - OPERATIONAL SLA: Support commitments, response times, or business hour terms.",
            "",
            "2. CONSTRAINT ISOLATION: Negative constraints ('no migration', 'no downtime') are high-risk failure points. You must flag every constraint prominently.",
            "",
            "3. CLIENT PSYCHOLOGY & PRIORITY: Infer what the client truly cares about (e.g. continuity & low operational risk vs cutting-edge experimentation).",
            "",
            "4. VERBATIM QUOTING: In exact_quote, you MUST extract the character-for-character exact snippet directly from the RFP. Do NOT paraphrase.",
        ],
    )
