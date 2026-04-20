from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.database.repository import EventRepository
from app.database.session import get_db

router = APIRouter(prefix="/feedback", tags=["feedback"])


class FeedbackRequest(BaseModel):
    sample_hash: str = Field(..., min_length=16, max_length=128)
    domain: str = Field(default="", max_length=255)
    source: str = Field(default="extension", max_length=64)
    current_risk_score: float = Field(default=0.0, ge=0.0, le=1.0)
    current_classification: str = Field(default="unknown", max_length=32)
    user_feedback: Literal["mark_not_risky", "report_risky"]
    reasons: list[str] = Field(default_factory=list, max_length=25)

    @field_validator("reasons")
    @classmethod
    def clamp_reasons(cls, values: list[str]) -> list[str]:
        return [str(value)[:240] for value in values[:25]]


@router.post("")
def submit_feedback(payload: FeedbackRequest, db: Session = Depends(get_db)) -> dict[str, object]:
    record = EventRepository(db).create_feedback(payload.model_dump())
    return {
        "status": "received",
        "review_status": record.review_status,
        "feedback_id": record.id,
        "message": "Feedback recorded for review",
    }
