from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class EmailAnalysisEvent(Base):
    __tablename__ = "email_analysis_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sample_hash: Mapped[str] = mapped_column(String(64), index=True)
    sender_hash: Mapped[str] = mapped_column(String(64), index=True)
    subject_hash: Mapped[str] = mapped_column(String(64), index=True)
    domain: Mapped[str] = mapped_column(String(255), index=True, default="")
    source: Mapped[str] = mapped_column(String(64), index=True, default="generic")
    risk_score: Mapped[float] = mapped_column(Float, index=True)
    classification: Mapped[str] = mapped_column(String(32), index=True)
    confidence: Mapped[str] = mapped_column(String(32), default="low")
    impersonated_brand: Mapped[str | None] = mapped_column(String(128), nullable=True)
    reasons_json: Mapped[str] = mapped_column(Text, default="[]")
    features_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )


class FeedbackEvent(Base):
    __tablename__ = "feedback_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sample_hash: Mapped[str] = mapped_column(String(64), index=True)
    domain: Mapped[str] = mapped_column(String(255), index=True, default="")
    source: Mapped[str] = mapped_column(String(64), index=True, default="extension")
    current_risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    current_classification: Mapped[str] = mapped_column(String(32), index=True)
    user_feedback: Mapped[str] = mapped_column(String(32), index=True)
    review_status: Mapped[str] = mapped_column(String(32), index=True, default="pending")
    reasons_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
