from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Iterable, List, Optional

from ..database.database import Database
from ..logging_config import get_logger

TransportFn = Callable[[Dict[str, Any]], None]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ResearchService:
    """High level helper for research/telemetry data."""

    SCHEMA_VERSION = 1

    def __init__(self, database: Database):
        self._db = database
        self._conn: sqlite3.Connection = database.conn
        self._conn.row_factory = sqlite3.Row
        self._logger = get_logger(__name__)

    # ------------------------------------------------------------------
    # Settings helpers
    # ------------------------------------------------------------------
    def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        cur = self._conn.execute("SELECT value FROM app_settings WHERE key=?", (key,))
        row = cur.fetchone()
        return row["value"] if row else default

    def set_setting(self, key: str, value: str) -> None:
        self._conn.execute(
            "INSERT INTO app_settings(key, value) VALUES(?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )
        self._conn.commit()

    def ensure_research_id(self) -> str:
        rid = self.get_setting("research_id")
        if rid:
            return rid
        rid = str(uuid.uuid4())
        self.set_setting("research_id", rid)
        return rid

    def is_opted_in(self) -> bool:
        return self.get_setting("research_opt_in", "0") == "1"

    def set_opt_in(self, enabled: bool) -> None:
        self.set_setting("research_opt_in", "1" if enabled else "0")

    def get_research_id(self) -> Optional[str]:
        return self.get_setting("research_id")

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------
    def lock_session(self, session_id: int) -> None:
        now = _utc_now()
        self._conn.execute(
            "UPDATE test_session SET status='locked', locked_at=? WHERE id=?",
            (now, session_id),
        )
        self._conn.commit()

        if self.get_setting("research_opt_in") == "1":
            for payload in self.build_research_payloads(session_id):
                self.enqueue_payload(payload)

    # ------------------------------------------------------------------
    # Payload construction
    # ------------------------------------------------------------------
    def build_research_payloads(self, session_id: int) -> List[Dict[str, Any]]:
        session = self._fetchone("SELECT * FROM test_session WHERE id=?", (session_id,))
        if not session:
            return []

        research_id = self.ensure_research_id()
        firearm = None
        if session["firearm_id"] is not None:
            firearm = self._fetchone(
                "SELECT * FROM firearm WHERE id=?", (session["firearm_id"],)
            )
        results = self._fetchall(
            "SELECT * FROM test_result WHERE test_session_id=?", (session_id,)
        )

        payloads: List[Dict[str, Any]] = []
        for result in results:
            recipe = self._fetchone(
                "SELECT * FROM load_recipe WHERE id=?", (result["load_recipe_id"],)
            )
            payloads.append(
                {
                    "schema_version": self.SCHEMA_VERSION,
                    "research_id": research_id,
                    "record_id": str(uuid.uuid4()),
                    "firearm": self._sanitize_firearm(firearm),
                    "components": self._component_payload(recipe),
                    "session": self._sanitize_session(session),
                    "result": self._sanitize_result(result),
                }
            )

        return payloads

    def _component_payload(self, recipe: Optional[sqlite3.Row]) -> Dict[str, Any]:
        if not recipe:
            return {}

        bullet = self._fetch_component("component_bullet", recipe["bullet_id"])
        powder = self._fetch_component("component_powder", recipe["powder_id"])
        primer = self._fetch_component("component_primer", recipe["primer_id"])
        case = self._fetch_component("component_case", recipe["case_id"])

        return {
            "bullet": self._sanitize_bullet(bullet),
            "powder": self._sanitize_powder(powder),
            "primer": self._sanitize_primer(primer),
            "case": self._sanitize_case(case),
            "load": {
                "case_firings": recipe["case_firings"],
                "powder_charge_gr": recipe["powder_charge_gr"],
                "col_mm": recipe["col_mm"],
                "jump_mm": recipe["jump_mm"],
                "created_at": recipe["created_at"],
            },
        }

    @staticmethod
    def _sanitize_firearm(row: Optional[sqlite3.Row]) -> Dict[str, Any]:
        if not row:
            return {}
        return {
            "caliber": row["caliber"],
            "barrel_length_mm": row["barrel_length_mm"],
            "twist": row["twist"],
            "muzzle_device": row["muzzle_device"],
            "muzzle_device_weight_g": row["muzzle_device_weight_g"],
        }

    @staticmethod
    def _sanitize_session(row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "distance_m": row["distance_m"],
            "temperature_c": row["temperature_c"],
            "chronograph_type": row["chronograph_type"],
            "status": row["status"],
            "started_at": row["started_at"],
            "locked_at": row["locked_at"],
        }

    @staticmethod
    def _sanitize_result(row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "shots_n": row["shots_n"],
            "velocity_avg_mps": row["velocity_avg_mps"],
            "velocity_sd_mps": row["velocity_sd_mps"],
            "velocity_es_mps": row["velocity_es_mps"],
            "group_size_mm": row["group_size_mm"],
            "group_moa": row["group_moa"],
            "pressure_signs_reported": row["pressure_signs_reported"],
        }

    @staticmethod
    def _sanitize_bullet(row: Optional[sqlite3.Row]) -> Optional[Dict[str, Any]]:
        if not row:
            return None
        return {
            "make": row["make"],
            "model": row["model"],
            "weight_gr": row["weight_gr"],
            "bc": row["bc"],
            "diameter_mm": row["diameter_mm"],
        }

    @staticmethod
    def _sanitize_powder(row: Optional[sqlite3.Row]) -> Optional[Dict[str, Any]]:
        if not row:
            return None
        return {
            "make": row["make"],
            "name": row["name"],
        }

    @staticmethod
    def _sanitize_primer(row: Optional[sqlite3.Row]) -> Optional[Dict[str, Any]]:
        if not row:
            return None
        return {
            "type": row["type"],
            "make": row["make"],
            "model": row["model"],
        }

    @staticmethod
    def _sanitize_case(row: Optional[sqlite3.Row]) -> Optional[Dict[str, Any]]:
        if not row:
            return None
        return {
            "make": row["make"],
            "model": row["model"],
        }

    # ------------------------------------------------------------------
    # Outbox helpers
    # ------------------------------------------------------------------
    def enqueue_payload(self, record: Dict[str, Any]) -> None:
        payload = json.dumps(record, ensure_ascii=False, separators=(",", ":"))
        self._conn.execute(
            "INSERT INTO research_outbox (created_at, payload_json, status) VALUES (?, ?, 'pending')",
            (_utc_now(), payload),
        )
        self._conn.commit()

    def send_pending(self, transport_fn: TransportFn) -> None:
        cur = self._conn.execute(
            "SELECT * FROM research_outbox WHERE status='pending' ORDER BY id"
        )
        rows = cur.fetchall()
        for row in rows:
            payload = json.loads(row["payload_json"])
            try:
                transport_fn(payload)
            except Exception as exc:  # noqa: BLE001 - we capture message for telemetry
                self._conn.execute(
                    "UPDATE research_outbox SET status='failed', retry_count=retry_count+1, "
                    "last_attempt_at=?, last_error=? WHERE id=?",
                    (_utc_now(), str(exc)[:500], row["id"]),
                )
                self._logger.warning("Research send failed for %s: %s", row["id"], exc)
            else:
                self._conn.execute(
                    "UPDATE research_outbox SET status='sent', last_attempt_at=?, last_error=NULL WHERE id=?",
                    (_utc_now(), row["id"]),
                )
        self._conn.commit()

    def retry_failed(self) -> None:
        self._conn.execute(
            "UPDATE research_outbox SET status='pending' WHERE status='failed'"
        )
        self._conn.commit()

    def get_outbox_summary(self) -> Dict[str, int]:
        counts: Dict[str, int] = {"pending": 0, "sent": 0, "failed": 0}
        cur = self._conn.execute(
            "SELECT status, COUNT(1) AS c FROM research_outbox GROUP BY status"
        )
        total = 0
        for row in cur.fetchall():
            status = row["status"]
            count = int(row["c"])
            counts[status] = count
            total += count
        counts["total"] = total
        return counts

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _fetchone(self, query: str, params: Iterable[Any]) -> Optional[sqlite3.Row]:
        cur = self._conn.execute(query, tuple(params))
        return cur.fetchone()

    def _fetchall(self, query: str, params: Iterable[Any]) -> List[sqlite3.Row]:
        cur = self._conn.execute(query, tuple(params))
        return cur.fetchall()

    def _fetch_component(
        self, table: str, component_id: Optional[int]
    ) -> Optional[sqlite3.Row]:
        if component_id is None:
            return None
        return self._fetchone(f"SELECT * FROM {table} WHERE id=?", (component_id,))
