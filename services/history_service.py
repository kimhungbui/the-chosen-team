"""
History Service — FPT Software Europe (Proposal Scorer).
Provides persistent backend storage, retrieval, filtering, deletion, and analytics
for proposal evaluation runs using an embedded, thread-safe SQLite database.
"""

import os
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

from schema.proposal_models import ProposalEvaluationReport, TrafficLight
from schema.history_models import (
    HistoryRecordSummary,
    HistoryRecordDetail,
    HistoryStats,
)

DEFAULT_DB_DIR = Path(__file__).resolve().parent.parent / "data"
DEFAULT_DB_PATH = DEFAULT_DB_DIR / "history.db"


def _normalize_traffic_light(val: Any) -> TrafficLight:
    """Safely convert any enum, string, or object into a canonical TrafficLight enum."""
    if isinstance(val, TrafficLight):
        return val
    if hasattr(val, "value"):
        val = val.value
    val_str = str(val).upper().strip()
    if "GREEN" in val_str:
        return TrafficLight.GREEN
    elif "RED" in val_str:
        return TrafficLight.RED
    return TrafficLight.YELLOW


class HistoryService:
    """
    Thread-safe SQLite storage engine for managing proposal audit runs and historical analytics.
    """

    def __init__(self, db_path: Optional[Union[str, Path]] = None):
        self.db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
        self._ensure_db_dir()
        self._init_db()

    def _ensure_db_dir(self) -> None:
        """Create parent directory if it does not exist."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def _get_connection(self) -> sqlite3.Connection:
        """Create a connection with WAL mode and row factory enabled."""
        conn = sqlite3.connect(
            str(self.db_path),
            check_same_thread=False,
            timeout=30.0,
        )
        conn.row_factory = sqlite3.Row
        # Enable Write-Ahead Logging for high concurrency and performance
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA busy_timeout = 5000;")
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_db(self) -> None:
        """Initialize evaluations schema and query indices."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS evaluations (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    rfp_title TEXT NOT NULL,
                    proposal_title TEXT NOT NULL,
                    overall_score_pct REAL NOT NULL,
                    overall_traffic_light TEXT NOT NULL,
                    engine_mode TEXT NOT NULL,
                    rfp_filename TEXT,
                    proposal_filename TEXT,
                    report_json TEXT NOT NULL,
                    weights_json TEXT,
                    metadata_json TEXT
                );
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_evaluations_timestamp ON evaluations(timestamp DESC);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_evaluations_traffic_light ON evaluations(overall_traffic_light);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_evaluations_rfp_title ON evaluations(rfp_title);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_evaluations_proposal_title ON evaluations(proposal_title);")
            conn.commit()

    def save_evaluation(
        self,
        report: Union[ProposalEvaluationReport, dict],
        weights: Optional[Dict[str, float]] = None,
        rfp_filename: Optional[str] = None,
        proposal_filename: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        record_id: Optional[str] = None,
        timestamp: Optional[str] = None,
    ) -> HistoryRecordDetail:
        """
        Persist a completed evaluation report to the database.
        Accepts either a ProposalEvaluationReport instance or raw dictionary.
        """
        # Ensure report is parsed as ProposalEvaluationReport
        if isinstance(report, dict):
            report_obj = ProposalEvaluationReport.model_validate(report)
            report_json_str = json.dumps(report)
        else:
            report_obj = report
            report_json_str = report_obj.model_dump_json()

        # Generate metadata fields
        rec_id = record_id or f"eval_{uuid.uuid4().hex[:12]}"
        rec_time = timestamp or datetime.now(timezone.utc).isoformat()
        rec_weights = weights or {}
        rec_metadata = metadata or {}

        # Extract values
        rfp_title = getattr(report_obj, "rfp_title", "Untitled RFP")
        proposal_title = getattr(report_obj, "proposal_title", "Untitled Proposal")
        score_pct = float(getattr(report_obj, "overall_score_pct", 0.0))
        tl_enum = _normalize_traffic_light(getattr(report_obj, "overall_traffic_light", TrafficLight.YELLOW))
        traffic_light_str = tl_enum.value

        engine_mode = getattr(report_obj, "engine_mode", "agno_llm")

        weights_json = json.dumps(rec_weights)
        metadata_json = json.dumps(rec_metadata)

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO evaluations (
                    id, timestamp, rfp_title, proposal_title,
                    overall_score_pct, overall_traffic_light, engine_mode,
                    rfp_filename, proposal_filename, report_json,
                    weights_json, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    timestamp = excluded.timestamp,
                    rfp_title = excluded.rfp_title,
                    proposal_title = excluded.proposal_title,
                    overall_score_pct = excluded.overall_score_pct,
                    overall_traffic_light = excluded.overall_traffic_light,
                    engine_mode = excluded.engine_mode,
                    rfp_filename = excluded.rfp_filename,
                    proposal_filename = excluded.proposal_filename,
                    report_json = excluded.report_json,
                    weights_json = excluded.weights_json,
                    metadata_json = excluded.metadata_json;
                """,
                (
                    rec_id,
                    rec_time,
                    rfp_title,
                    proposal_title,
                    score_pct,
                    traffic_light_str,
                    engine_mode,
                    rfp_filename,
                    proposal_filename,
                    report_json_str,
                    weights_json,
                    metadata_json,
                ),
            )
            conn.commit()

        return HistoryRecordDetail(
            id=rec_id,
            timestamp=rec_time,
            rfp_title=rfp_title,
            proposal_title=proposal_title,
            overall_score_pct=score_pct,
            overall_traffic_light=tl_enum,
            engine_mode=engine_mode,
            rfp_filename=rfp_filename,
            proposal_filename=proposal_filename,
            report=report_obj,
            weights=rec_weights,
            metadata=rec_metadata,
        )

    def get_history(
        self,
        limit: int = 50,
        offset: int = 0,
        search_query: Optional[str] = None,
        traffic_light: Optional[Union[TrafficLight, str]] = None,
        engine_mode: Optional[str] = None,
    ) -> List[HistoryRecordSummary]:
        """
        Query lightweight history records for list and table displays.
        Excludes full report JSON for optimal query speed.
        """
        query = """
            SELECT id, timestamp, rfp_title, proposal_title,
                   overall_score_pct, overall_traffic_light, engine_mode,
                   rfp_filename, proposal_filename
            FROM evaluations
            WHERE 1=1
        """
        params: List[Any] = []

        if traffic_light:
            tl_val = _normalize_traffic_light(traffic_light).value
            query += " AND overall_traffic_light = ?"
            params.append(tl_val)

        if engine_mode:
            query += " AND engine_mode = ?"
            params.append(engine_mode)

        if search_query and search_query.strip():
            sq = f"%{search_query.strip().lower()}%"
            query += """
                AND (
                    LOWER(rfp_title) LIKE ?
                    OR LOWER(proposal_title) LIKE ?
                    OR LOWER(COALESCE(rfp_filename, '')) LIKE ?
                    OR LOWER(COALESCE(proposal_filename, '')) LIKE ?
                )
            """
            params.extend([sq, sq, sq, sq])

        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with self._get_connection() as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

        results = []
        for r in rows:
            results.append(
                HistoryRecordSummary(
                    id=r["id"],
                    timestamp=r["timestamp"],
                    rfp_title=r["rfp_title"],
                    proposal_title=r["proposal_title"],
                    overall_score_pct=float(r["overall_score_pct"]),
                    overall_traffic_light=_normalize_traffic_light(r["overall_traffic_light"]),
                    engine_mode=r["engine_mode"],
                    rfp_filename=r["rfp_filename"],
                    proposal_filename=r["proposal_filename"],
                )
            )
        return results

    def get_evaluation_by_id(self, record_id: str) -> Optional[HistoryRecordDetail]:
        """
        Retrieve a single evaluation record in its entirety, including full Pydantic report.
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT id, timestamp, rfp_title, proposal_title,
                       overall_score_pct, overall_traffic_light, engine_mode,
                       rfp_filename, proposal_filename, report_json,
                       weights_json, metadata_json
                FROM evaluations
                WHERE id = ?;
                """,
                (record_id,),
            )
            row = cursor.fetchone()

        if not row:
            return None

        # Parse JSON blobs
        report_data = json.loads(row["report_json"])
        report_obj = ProposalEvaluationReport.model_validate(report_data)

        weights = json.loads(row["weights_json"]) if row["weights_json"] else {}
        metadata = json.loads(row["metadata_json"]) if row["metadata_json"] else {}

        return HistoryRecordDetail(
            id=row["id"],
            timestamp=row["timestamp"],
            rfp_title=row["rfp_title"],
            proposal_title=row["proposal_title"],
            overall_score_pct=float(row["overall_score_pct"]),
            overall_traffic_light=_normalize_traffic_light(row["overall_traffic_light"]),
            engine_mode=row["engine_mode"],
            rfp_filename=row["rfp_filename"],
            proposal_filename=row["proposal_filename"],
            report=report_obj,
            weights=weights,
            metadata=metadata,
        )

    def delete_evaluation(self, record_id: str) -> bool:
        """
        Delete an evaluation record by ID. Returns True if deleted, False if record was not found.
        """
        with self._get_connection() as conn:
            cursor = conn.execute("DELETE FROM evaluations WHERE id = ?;", (record_id,))
            conn.commit()
            return cursor.rowcount > 0

    def clear_history(self) -> int:
        """
        Remove all stored evaluation records. Returns the total number of records deleted.
        """
        with self._get_connection() as conn:
            cursor = conn.execute("DELETE FROM evaluations;")
            conn.commit()
            return cursor.rowcount

    def get_stats(self) -> HistoryStats:
        """
        Compute real-time aggregate statistics across all recorded evaluations.
        """
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT
                    COUNT(*) as total_count,
                    COALESCE(AVG(overall_score_pct), 0.0) as avg_score,
                    SUM(CASE WHEN overall_traffic_light = 'GREEN' THEN 1 ELSE 0 END) as count_green,
                    SUM(CASE WHEN overall_traffic_light = 'YELLOW' THEN 1 ELSE 0 END) as count_yellow,
                    SUM(CASE WHEN overall_traffic_light = 'RED' THEN 1 ELSE 0 END) as count_red,
                    MAX(timestamp) as latest_ts
                FROM evaluations;
            """)
            row = cursor.fetchone()

        if not row or row["total_count"] == 0:
            return HistoryStats()

        return HistoryStats(
            total_evaluations=int(row["total_count"]),
            average_score_pct=round(float(row["avg_score"]), 1),
            count_green=int(row["count_green"] or 0),
            count_yellow=int(row["count_yellow"] or 0),
            count_red=int(row["count_red"] or 0),
            latest_timestamp=row["latest_ts"],
        )

    def export_history_json(self, limit: int = 100) -> str:
        """
        Export historical records as a structured JSON string.
        """
        summaries = self.get_history(limit=limit)
        full_records = []
        for s in summaries:
            detail = self.get_evaluation_by_id(s.id)
            if detail:
                full_records.append(detail.model_dump())
        return json.dumps(full_records, indent=2, default=str)


# Default shared service instance
history_service = HistoryService()

# Helper module-level functions
def save_evaluation(
    report: Union[ProposalEvaluationReport, dict],
    weights: Optional[Dict[str, float]] = None,
    rfp_filename: Optional[str] = None,
    proposal_filename: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    record_id: Optional[str] = None,
) -> HistoryRecordDetail:
    return history_service.save_evaluation(
        report=report,
        weights=weights,
        rfp_filename=rfp_filename,
        proposal_filename=proposal_filename,
        metadata=metadata,
        record_id=record_id,
    )


def get_history(
    limit: int = 50,
    offset: int = 0,
    search_query: Optional[str] = None,
    traffic_light: Optional[Union[TrafficLight, str]] = None,
    engine_mode: Optional[str] = None,
) -> List[HistoryRecordSummary]:
    return history_service.get_history(
        limit=limit,
        offset=offset,
        search_query=search_query,
        traffic_light=traffic_light,
        engine_mode=engine_mode,
    )


def get_evaluation_by_id(record_id: str) -> Optional[HistoryRecordDetail]:
    return history_service.get_evaluation_by_id(record_id)


def delete_evaluation(record_id: str) -> bool:
    return history_service.delete_evaluation(record_id)


def clear_history() -> int:
    return history_service.clear_history()


def get_history_stats() -> HistoryStats:
    return history_service.get_stats()
