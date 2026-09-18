"""
API Package — Proposal Scorer.
Exposes FastAPI router and application for REST integrations.
"""

from api.router import router
from api.server import app

__all__ = ["router", "app"]
