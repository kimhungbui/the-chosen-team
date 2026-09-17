from agno.agent import Agent
from agents.assistant import get_model
from models.schemas import ComplianceMatrix

def create_compliance_auditor_agent() -> Agent:
    """
    Creates an Agno Agent that audits a draft proposal against each extracted RFP requirement.
    """
    return Agent(
        name="Compliance Auditor",
        model=get_model("gemini-2.5-flash"),
        output_schema=ComplianceMatrix,
        instructions=[
            "You are a rigorous procurement compliance auditor.",
            "You will receive a list of explicit RFP requirements alongside a vendor draft proposal.",
            "Evaluate the proposal against EVERY requirement in the checklist:",
            " - Mark MET if the requirement is fully, specifically, and unambiguously addressed.",
            " - Mark PARTIALLY_MET if the proposal mentions it vaguely without key specifics.",
            " - Mark MISSING if the requirement or constraint is completely omitted.",
            " - Mark CONTRADICTED if the proposal violates an explicit constraint (e.g. proposes database migration when prohibited) or expands scope unrealistically.",
            " - Mark DEFERRED if the proposal defers critical information (e.g. pricing 'to be discussed', timeline 'in due course').",
            "Whenever possible, extract an exact verbatim quote from the proposal into proposal_quote.",
            "Provide a precise gap_analysis explaining why the status was assigned.",
        ],
    )
