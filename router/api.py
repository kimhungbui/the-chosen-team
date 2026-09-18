"""
Router Compatibility Module.
Re-exports the unified FastAPI application from api.server to ensure
all history, stats, and evaluation endpoints are available regardless of launch command.
"""

from api.server import app
from services.scoring_engine import DEFAULT_WEIGHTS, evaluate_proposal
from services.document_parser import (
    UnsupportedDocumentTypeError,
    UnreadableDocumentError,
    parse_document,
)

__all__ = [
    "app",
    "DEFAULT_WEIGHTS",
    "evaluate_proposal",
    "UnsupportedDocumentTypeError",
    "UnreadableDocumentError",
    "parse_document",
]
