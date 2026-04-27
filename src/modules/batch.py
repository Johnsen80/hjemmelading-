"""Lightweight in-memory model for a load development batch."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class BatchSession:
    """One recorded range or chrono session for a batch."""

    session_date: str
    session_type: str = "range"
    notes: str = ""
    group_size_mm: Optional[float] = None
    group_size_moa: Optional[float] = None
    shot_count: Optional[int] = None
    chronograph_import_id: Optional[int] = None
    analysis: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BatchAttachment:
    """Stored image or document linked to a batch."""

    file_path: str
    attachment_type: str = "photo"
    caption: str = ""


@dataclass
class Batch:
    """Canonical batch object used by the UI and analyzer."""

    batch_id: int
    rifle_id: int
    batch_number: str = ""
    batch_name: str = ""
    ammo_data: Dict[str, Any] = field(default_factory=dict)
    sim_data: Dict[str, Any] = field(default_factory=dict)
    status: str = "active"
    ammo_type: str = "rifle"
    created_at: str = ""
    notes: str = ""
    sessions: List[BatchSession] = field(default_factory=list)
    attachments: List[BatchAttachment] = field(default_factory=list)
    analysis: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now().isoformat(timespec="seconds")

    def add_session(self, session: BatchSession | Dict[str, Any]) -> None:
        if isinstance(session, dict):
            session = BatchSession(**session)
        self.sessions.append(session)

    def add_attachment(self, attachment: BatchAttachment | Dict[str, Any]) -> None:
        if isinstance(attachment, dict):
            attachment = BatchAttachment(**attachment)
        self.attachments.append(attachment)

    def update_notes(self, notes: str) -> None:
        self.notes = notes

    def to_dict(self) -> Dict[str, Any]:
        return {
            "batch_id": self.batch_id,
            "rifle_id": self.rifle_id,
            "batch_number": self.batch_number,
            "batch_name": self.batch_name,
            "ammo_data": self.ammo_data,
            "sim_data": self.sim_data,
            "status": self.status,
            "ammo_type": self.ammo_type,
            "created_at": self.created_at,
            "notes": self.notes,
            "sessions": [session.__dict__ for session in self.sessions],
            "attachments": [attachment.__dict__ for attachment in self.attachments],
            "analysis": self.analysis,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Batch":
        batch = Batch(
            batch_id=data.get("batch_id", 0),
            rifle_id=data.get("rifle_id", 0),
            batch_number=data.get("batch_number", ""),
            batch_name=data.get("batch_name", ""),
            ammo_data=data.get("ammo_data", {}),
            sim_data=data.get("sim_data", {}),
            status=data.get("status", "active"),
            ammo_type=data.get("ammo_type", "rifle"),
            created_at=data.get("created_at", ""),
            notes=data.get("notes", ""),
            analysis=data.get("analysis", {}),
        )
        for session in data.get("sessions", []):
            batch.add_session(session)
        for attachment in data.get("attachments", []):
            batch.add_attachment(attachment)
        return batch
