"""
API Service Implementation — Proposal Scorer & History Management.
Provides a clean, strongly-typed interface layer fulfilling the frontend API contract.
Can be invoked directly from Python/Streamlit or served over HTTP (FastAPI).
"""

import time
import traceback
from typing import Dict, Optional, Any, Union, List

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
from schema.proposal_models import ProposalEvaluationReport
from services.scoring_engine import evaluate_proposal, DEFAULT_WEIGHTS
from services.history_service import history_service, HistoryService


class ProposalScorerAPI:
    """
    Unified frontend API contract service for proposal evaluation and audit history.
    """

    def __init__(self, history_backend: Optional[HistoryService] = None):
        self.history = history_backend or history_service

    def evaluate(
        self,
        request: Union[EvaluateProposalRequest, Dict[str, Any]],
    ) -> EvaluateProposalResponse:
        """
        Execute full proposal evaluation and optionally persist to history database.
        Returns a standardized EvaluateProposalResponse contract.
        """
        # Validate and coerce input
        req = request if isinstance(request, EvaluateProposalRequest) else EvaluateProposalRequest.model_validate(request)

        start_time = time.perf_counter()
        try:
            report: ProposalEvaluationReport = evaluate_proposal(
                rfp_text=req.rfp_text,
                proposal_text=req.proposal_text,
                proposal_title=req.proposal_title,
                rfp_title=req.rfp_title,
                custom_weights=req.custom_weights or DEFAULT_WEIGHTS,
                force_fallback=not req.use_llm_mode,
                rfp_metrics=req.rfp_metrics,
                proposal_metrics=req.proposal_metrics,
                allow_fallback_on_error=req.allow_fallback_on_error,
            )

            execution_ms = round((time.perf_counter() - start_time) * 1000, 2)
            is_fallback = getattr(report, "engine_mode", "") == "rule_engine" and req.use_llm_mode

            history_id = None
            if req.auto_save_history:
                saved_record = self.history.save_evaluation(
                    report=report,
                    weights=req.custom_weights or DEFAULT_WEIGHTS,
                    rfp_filename=req.rfp_filename,
                    proposal_filename=req.proposal_filename,
                    metadata=req.metadata,
                )
                history_id = saved_record.id

            return EvaluateProposalResponse(
                success=True,
                report=report,
                history_id=history_id,
                engine_mode=getattr(report, "engine_mode", "rule_engine"),
                execution_time_ms=execution_ms,
                is_fallback=is_fallback,
                error_message=None,
                error_traceback=None,
            )

        except Exception as exc:
            execution_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return EvaluateProposalResponse(
                success=False,
                report=None,
                history_id=None,
                engine_mode="error",
                execution_time_ms=execution_ms,
                is_fallback=False,
                error_message=str(exc),
                error_traceback=traceback.format_exc(),
            )

    def list_history(
        self,
        request: Optional[Union[HistoryListRequest, Dict[str, Any]]] = None,
    ) -> HistoryListResponse:
        """
        Query paginated historical evaluation summaries with optional search and filters.
        """
        if request is None:
            req = HistoryListRequest()
        elif isinstance(request, HistoryListRequest):
            req = request
        else:
            req = HistoryListRequest.model_validate(request)

        items = self.history.get_history(
            limit=req.limit,
            offset=req.offset,
            search_query=req.search_query,
            traffic_light=req.traffic_light,
            engine_mode=req.engine_mode,
        )

        stats = self.history.get_stats()
        return HistoryListResponse(
            success=True,
            items=items,
            total_count=stats.total_evaluations,
            limit=req.limit,
            offset=req.offset,
        )

    def get_history_detail(self, record_id: str) -> HistoryDetailResponse:
        """
        Retrieve complete historical report by unique record ID.
        """
        record = self.history.get_evaluation_by_id(record_id)
        if not record:
            return HistoryDetailResponse(
                success=False,
                record=None,
                error_message=f"Evaluation record '{record_id}' not found.",
            )
        return HistoryDetailResponse(success=True, record=record)

    def delete_history_item(self, record_id: str) -> HistoryDeleteResponse:
        """
        Delete a historical evaluation record.
        """
        deleted = self.history.delete_evaluation(record_id)
        if not deleted:
            return HistoryDeleteResponse(
                success=False,
                deleted_id=record_id,
                message=f"Evaluation record '{record_id}' not found or already deleted.",
            )
        return HistoryDeleteResponse(
            success=True,
            deleted_id=record_id,
            message=f"Evaluation record '{record_id}' permanently deleted.",
        )

    def clear_all_history(self) -> HistoryClearResponse:
        """
        Wipe all stored evaluation history.
        """
        count = self.history.clear_history()
        return HistoryClearResponse(
            success=True,
            records_deleted=count,
            message=f"Cleared {count} historical evaluation records.",
        )

    def get_stats(self) -> HistoryStatsResponse:
        """
        Return real-time aggregate statistics.
        """
        stats = self.history.get_stats()
        return HistoryStatsResponse(success=True, stats=stats)

    def export_history(self, limit: int = 100) -> str:
        """
        Export historical records as formatted JSON.
        """
        return self.history.export_history_json(limit=limit)


# Default shared singleton instance
api_service = ProposalScorerAPI()
