"""
Pydantic Data Models for Proposal Evaluation History Storage.
Defines schemas for historical run summaries, detailed historical records, and aggregate statistics.
"""

from typing import Dict, Optional, Any, List
from pydantic import BaseModel, Field
from schema.proposal_models import TrafficLight, ProposalEvaluationReport


class HistoryRecordSummary(BaseModel):
    """Lightweight metadata model for displaying evaluation history in lists or tables."""
    id: str = Field(..., description="Unique evaluation record ID (e.g., eval_abc123)")
    timestamp: str = Field(..., description="ISO-8601 formatted timestamp of when evaluation occurred")
    rfp_title: str = Field(..., description="Title of the client RFP document")
    proposal_title: str = Field(..., description="Title of the draft proposal document")
    overall_score_pct: float = Field(..., description="Overall weighted score percentage (0.0 - 100.0)")
    overall_traffic_light: TrafficLight = Field(..., description="Status rating: GREEN, YELLOW, or RED")
    engine_mode: str = Field("agno_llm", description="Evaluation engine used (agno_llm or rule_engine)")
    rfp_filename: Optional[str] = Field(None, description="Original filename of the RFP")
    proposal_filename: Optional[str] = Field(None, description="Original filename of the proposal")


class HistoryRecordDetail(HistoryRecordSummary):
    """Comprehensive evaluation record containing full report, custom weights, and telemetry metadata."""
    report: ProposalEvaluationReport = Field(..., description="Complete 7-criteria evaluation report object")
    weights: Dict[str, float] = Field(default_factory=dict, description="Rubric weights configured during run")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional telemetry, execution notes, or custom tags")


class HistoryStats(BaseModel):
    """Aggregate statistics for historical proposal evaluations."""
    total_evaluations: int = Field(0, description="Total number of stored evaluation runs")
    average_score_pct: float = Field(0.0, description="Mean overall score across all recorded runs")
    count_green: int = Field(0, description="Number of proposals rated GREEN (>=80%)")
    count_yellow: int = Field(0, description="Number of proposals rated YELLOW (50-79%)")
    count_red: int = Field(0, description="Number of proposals rated RED (<50%)")
    latest_timestamp: Optional[str] = Field(None, description="Timestamp of the most recent evaluation run")
