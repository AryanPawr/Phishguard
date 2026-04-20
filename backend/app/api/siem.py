from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import require_admin
from app.database.repository import EventRepository
from app.database.session import get_db

router = APIRouter(prefix="/siem", tags=["siem"])


@router.get("/export")
def export_siem(
    limit: int = 100,
    _: str = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    events = EventRepository(db).siem_events(limit)
    return {
        "schema": "phishguard.siem.v1",
        "format": "json",
        "count": len(events),
        "events": events,
    }
