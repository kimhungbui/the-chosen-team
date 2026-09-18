"""
FastAPI Router — Proposal Scorer & Evaluation History.
Exposes RESTful endpoints conforming to the frontend API contract.
Supports file upload (PDF/Markdown/Text), custom weights, and complete history management.
"""

import json
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Request, status

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
from services.document_parser import (
    UnsupportedDocumentTypeError,
    UnreadableDocumentError,
    parse_document,
)
from services.scoring_engine import DEFAULT_WEIGHTS

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
async def evaluate_proposal_endpoint(request: Request):
    """
    Evaluate a draft proposal against an RFP document.
    Accepts both:
    1. 'multipart/form-data' with 'rfp_file', 'proposal_file', optional 'weights' JSON string.
    2. 'application/json' with EvaluateProposalRequest payload (raw text strings).
    Automatically saves the evaluation into SQLite history and returns wrapped response.
    """
    content_type = request.headers.get("content-type", "").lower()

    # Case 1: JSON Payload
    if "application/json" in content_type:
        try:
            data = await request.json()
            req = EvaluateProposalRequest.model_validate(data)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid JSON request body: {exc}",
            ) from exc

        response = api_service.evaluate(req)
        if not response.success and response.error_message and not response.report:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=response.error_message,
            )
        return response

    # Case 2: Multipart Form-Data (File Upload)
    elif "multipart/form-data" in content_type:
        form = await request.form()
        rfp_file = form.get("rfp_file")
        proposal_file = form.get("proposal_file")
        weights = form.get("weights")
        auto_save_history = form.get("auto_save_history", "true")

        if not rfp_file or not hasattr(rfp_file, "filename"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Field 'rfp_file' is required.",
            )
        if not proposal_file or not hasattr(proposal_file, "filename"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Field 'proposal_file' is required.",
            )

        custom_weights = DEFAULT_WEIGHTS
        if weights is not None and str(weights).strip():
            try:
                custom_weights = json.loads(str(weights))
            except json.JSONDecodeError as exc:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="weights must be a valid JSON object.",
                ) from exc

            if (
                not isinstance(custom_weights, dict)
                or custom_weights.keys() != DEFAULT_WEIGHTS.keys()
                or any(
                    type(value) not in (int, float) or not 0 <= value <= 100
                    for value in custom_weights.values()
                )
                or abs(sum(custom_weights.values()) - 100) > 0.1
            ):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Provide all 7 criterion weights between 0 and 100, totaling 100.",
                )

        try:
            rfp_bytes = await rfp_file.read()
            proposal_bytes = await proposal_file.read()
            rfp_text, rfp_metrics = parse_document(rfp_file.filename or "", rfp_bytes)
            proposal_text, proposal_metrics = parse_document(
                proposal_file.filename or "", proposal_bytes
            )
        except UnsupportedDocumentTypeError as exc:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=str(exc),
            ) from exc
        except UnreadableDocumentError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            ) from exc

        is_auto_save = str(auto_save_history).lower() not in ("false", "0", "no")
        req = EvaluateProposalRequest(
            rfp_text=rfp_text,
            proposal_text=proposal_text,
            proposal_title=proposal_file.filename or "Draft Proposal",
            rfp_title=rfp_file.filename or "Client RFP",
            custom_weights=custom_weights,
            rfp_filename=rfp_file.filename,
            proposal_filename=proposal_file.filename,
            rfp_metrics=rfp_metrics,
            proposal_metrics=proposal_metrics,
            use_llm_mode=True,
            allow_fallback_on_error=True,
            auto_save_history=is_auto_save,
        )

        response = api_service.evaluate(req)
        if not response.success and response.error_message and not response.report:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=response.error_message,
            )
        return response

    else:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported Content-Type '{content_type}'. Expected 'multipart/form-data' or 'application/json'.",
        )


@router.post("/evaluate/text", response_model=EvaluateProposalResponse)
def evaluate_proposal_text_endpoint(request: EvaluateProposalRequest):
    """
    Dedicated endpoint for raw JSON text evaluations.
    """
    response = api_service.evaluate(request)
    if not response.success and response.error_message and not response.report:
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
