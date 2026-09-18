"""
FastAPI Router — Proposal Scorer & Evaluation History.
Exposes RESTful endpoints conforming to the frontend API contract.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status

from schema.api_models import (
    EvaluateProposalRequest,
    EvaluateProposalResponse,
    HistoryListRequest,
    HistoryListResponse,
    HistoryDetailResponse,
    HistoryDeleteResponse,
    HistoryClearResponse,
    HistoryStatsResponse,
)
from services.api_service import api_service

router = APIRouter(tags=["Proposal Evaluation & History"])


@router.get("/health")
def health_check():
    """Health check endpoint to verify backend service status."""
    return {
        "status": "healthy",
        "service": "Proposal Scorer API",
        "version": "1.0.0",
    }


@router.post("/evaluate", response_model=EvaluateProposalResponse)
def evaluate_proposal_endpoint(request: EvaluateProposalRequest):
    """
    Evaluate a draft proposal against an RFP using the 2-Stage Multi-Agent pipeline
    or dynamic offline rule engine, with optional automatic history storage.
    """
    response = api_service.evaluate(request)
    if not response.success and response.error_message and not response.report:
        # If it failed completely without fallback
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=response.error_message,
        )
    return response


@router.get("/history", response_model=HistoryListResponse)
def list_history_endpoint(
    limit: int = Query(50, ge=1, le=500, description="Max records to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    search: Optional[str] = Query(None, description="Search across titles and filenames"),
    traffic_light: Optional[str] = Query(None, description="Filter by status (GREEN, YELLOW, RED)"),
    engine_mode: Optional[str] = Query(None, description="Filter by engine mode (agno_llm, rule_engine)"),
):
    """List historical proposal evaluations with pagination and filtering."""
    req = HistoryListRequest(
        limit=limit,
        offset=offset,
        search_query=search,
        traffic_light=traffic_light,
        engine_mode=engine_mode,
    )
    return api_service.list_history(req)


@router.get("/history/{record_id}", response_model=HistoryDetailResponse)
def get_history_detail_endpoint(record_id: str):
    """Retrieve full evaluation report and telemetry by record ID."""
    res = api_service.get_history_detail(record_id)
    if not res.success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=res.error_message or f"Record '{record_id}' not found.",
        )
    return res


@router.delete("/history/{record_id}", response_model=HistoryDeleteResponse)
def delete_history_endpoint(record_id: str):
    """Delete a specific historical evaluation record."""
    res = api_service.delete_history_item(record_id)
    if not res.success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=res.message,
        )
    return res


@router.delete("/history", response_model=HistoryClearResponse)
def clear_history_endpoint():
    """Clear all historical evaluation records."""
    return api_service.clear_all_history()


@router.get("/stats", response_model=HistoryStatsResponse)
def get_history_stats_endpoint():
    """Get aggregate historical evaluation analytics."""
    return api_service.get_stats()
