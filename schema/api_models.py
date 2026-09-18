"""
Pydantic API Contract Models — Proposal Scorer & History Management.
Defines strongly-typed request and response contracts for frontend consumption,
REST endpoints, and inter-service communication.
"""

from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
from schema.proposal_models import ProposalEvaluationReport, TrafficLight
from schema.history_models import HistoryRecordSummary, HistoryRecordDetail, HistoryStats


# ---------------------------------------------------------------------------
# Proposal Evaluation API Contracts
# ---------------------------------------------------------------------------

class EvaluateProposalRequest(BaseModel):
    """Client request payload to evaluate a draft proposal against an RFP."""
    rfp_text: str = Field(..., description="Raw text content of the Client RFP document")
    proposal_text: str = Field(..., description="Raw text content of the Draft Proposal document")
    proposal_title: str = Field("Draft Proposal", description="Title or filename of the proposal")
    rfp_title: str = Field("Client RFP", description="Title or filename of the RFP")
    custom_weights: Optional[Dict[str, float]] = Field(
        None,
        description="Optional 7-criterion weights map summing to 100%. Defaults to balanced preset."
    )
    use_llm_mode: bool = Field(
        True,
        description="True to use Agno Gemini Multi-Agent engine; False for offline deterministic rule engine."
    )
    allow_fallback_on_error: bool = Field(
        True,
        description="Whether to automatically switch to rule engine if LLM quota or connection fails."
    )
    auto_save_history: bool = Field(
        True,
        description="Whether to automatically persist the resulting report into the History database."
    )
    rfp_filename: Optional[str] = Field(None, description="Original uploaded filename of the RFP")
    proposal_filename: Optional[str] = Field(None, description="Original uploaded filename of the Proposal")
    rfp_metrics: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Pre-extracted RFP document metrics")
    proposal_metrics: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Pre-extracted proposal document metrics")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Custom tags, auditor IDs, or session metadata")


class EvaluateProposalResponse(BaseModel):
    """Standardized response contract for proposal evaluation."""
    success: bool = Field(..., description="True if evaluation completed successfully")
    report: Optional[ProposalEvaluationReport] = Field(None, description="Comprehensive 7-criterion evaluation report")
    history_id: Optional[str] = Field(None, description="Database record ID if report was saved to history")
    engine_mode: str = Field("agno_llm", description="Engine used ('agno_llm' or 'rule_engine')")
    execution_time_ms: float = Field(0.0, description="Execution time in milliseconds")
    is_fallback: bool = Field(False, description="True if engine automatically fell back to rule engine")
    error_message: Optional[str] = Field(None, description="Human-readable error description if failed")
    error_traceback: Optional[str] = Field(None, description="Diagnostic traceback details for debugging")


# ---------------------------------------------------------------------------
# History Management API Contracts
# ---------------------------------------------------------------------------

class HistoryListRequest(BaseModel):
    """Query parameters for retrieving paginated evaluation history."""
    limit: int = Field(50, ge=1, le=500, description="Maximum number of historical records to return")
    offset: int = Field(0, ge=0, description="Offset for pagination")
    search_query: Optional[str] = Field(None, description="Filter across RFP/proposal titles and filenames")
    traffic_light: Optional[str] = Field(None, description="Filter by status: GREEN, YELLOW, or RED")
    engine_mode: Optional[str] = Field(None, description="Filter by engine mode: agno_llm or rule_engine")


class HistoryListResponse(BaseModel):
    """Response containing a page of lightweight evaluation summaries."""
    success: bool = Field(True)
    items: List[HistoryRecordSummary] = Field(default_factory=list, description="List of evaluation summaries")
    total_count: int = Field(0, description="Total records matching query in database")
    limit: int = Field(50, description="Page limit")
    offset: int = Field(0, description="Page offset")


class HistoryDetailResponse(BaseModel):
    """Response containing full evaluation report and telemetry by ID."""
    success: bool = Field(..., description="True if record was found")
    record: Optional[HistoryRecordDetail] = Field(None, description="Full historical record including 7 rubric criteria")
    error_message: Optional[str] = Field(None, description="Error message if not found")


class HistoryDeleteResponse(BaseModel):
    """Response contract when deleting a specific history entry."""
    success: bool = Field(...)
    deleted_id: str = Field(...)
    message: str = Field("Record deleted successfully")


class HistoryClearResponse(BaseModel):
    """Response contract when clearing all history records."""
    success: bool = Field(...)
    records_deleted: int = Field(..., description="Total number of deleted records")
    message: str = Field("History cleared successfully")


class HistoryStatsResponse(BaseModel):
    """Response containing aggregate evaluation metrics."""
    success: bool = Field(True)
    stats: HistoryStats = Field(..., description="Real-time aggregate historical metrics")
