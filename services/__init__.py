"""
Services Package — Proposal Scorer.
Provides evaluation scoring engine and history management service.
"""

from services.scoring_engine import (
    evaluate_proposal,
    DEFAULT_WEIGHTS,
    get_traffic_light,
    normalize_criterion_id,
)
from services.history_service import (
    HistoryService,
    history_service,
    save_evaluation,
    get_history,
    get_evaluation_by_id,
    delete_evaluation,
    clear_history,
    get_history_stats,
)

__all__ = [
    "evaluate_proposal",
    "DEFAULT_WEIGHTS",
    "get_traffic_light",
    "normalize_criterion_id",
    "HistoryService",
    "history_service",
    "save_evaluation",
    "get_history",
    "get_evaluation_by_id",
    "delete_evaluation",
    "clear_history",
    "get_history_stats",
]
