from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.database.models import EmailAnalysisEvent, FeedbackEvent


class EventRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_event(self, event: dict[str, Any]) -> EmailAnalysisEvent:
        record = EmailAnalysisEvent(
            sample_hash=event["sample_hash"],
            sender_hash=event["sender_hash"],
            subject_hash=event["subject_hash"],
            domain=event.get("domain", ""),
            source=event.get("source", "generic"),
            risk_score=float(event["risk_score"]),
            classification=event["classification"],
            confidence=event["confidence"],
            impersonated_brand=event.get("impersonated_brand"),
            reasons_json=json.dumps(event.get("reasons", [])),
            features_json=json.dumps(event.get("features", {})),
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def summary(self) -> dict[str, Any]:
        total = self.db.scalar(select(func.count()).select_from(EmailAnalysisEvent)) or 0
        phishing = self.db.scalar(
            select(func.count()).where(EmailAnalysisEvent.classification == "phishing")
        ) or 0
        suspicious = self.db.scalar(
            select(func.count()).where(EmailAnalysisEvent.classification == "suspicious")
        ) or 0
        safe = self.db.scalar(select(func.count()).where(EmailAnalysisEvent.classification == "safe")) or 0
        average_risk = self.db.scalar(select(func.avg(EmailAnalysisEvent.risk_score))) or 0.0
        return {
            "total_events": total,
            "phishing": phishing,
            "suspicious": suspicious,
            "safe": safe,
            "average_risk": round(float(average_risk), 4),
        }

    def recent(self, limit: int = 25) -> list[dict[str, Any]]:
        rows = self.db.scalars(
            select(EmailAnalysisEvent)
            .order_by(desc(EmailAnalysisEvent.created_at))
            .limit(min(limit, 100))
        ).all()
        return [self._serialize(row) for row in rows]

    def risk_trends(self, days: int = 14) -> list[dict[str, Any]]:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        rows = self.db.execute(
            select(
                func.date(EmailAnalysisEvent.created_at).label("day"),
                func.count().label("count"),
                func.avg(EmailAnalysisEvent.risk_score).label("avg_risk"),
            )
            .where(EmailAnalysisEvent.created_at >= since)
            .group_by("day")
            .order_by("day")
        ).all()
        return [
            {"day": str(day), "count": int(count), "average_risk": round(float(avg_risk or 0), 4)}
            for day, count, avg_risk in rows
        ]

    def top_brands(self, limit: int = 10) -> list[dict[str, Any]]:
        rows = self.db.execute(
            select(
                EmailAnalysisEvent.impersonated_brand,
                func.count().label("count"),
                func.avg(EmailAnalysisEvent.risk_score).label("avg_risk"),
            )
            .where(EmailAnalysisEvent.impersonated_brand.is_not(None))
            .group_by(EmailAnalysisEvent.impersonated_brand)
            .order_by(desc("count"))
            .limit(min(limit, 25))
        ).all()
        return [
            {
                "brand": str(brand),
                "count": int(count),
                "average_risk": round(float(avg_risk or 0), 4),
            }
            for brand, count, avg_risk in rows
        ]

    def siem_events(self, limit: int = 100) -> list[dict[str, Any]]:
        return [self._to_siem(row) for row in self.db.scalars(
            select(EmailAnalysisEvent)
            .order_by(desc(EmailAnalysisEvent.created_at))
            .limit(min(limit, 1000))
        ).all()]

    def recent_risk_events(self, limit: int = 40) -> list[dict[str, Any]]:
        rows = self.db.scalars(
            select(EmailAnalysisEvent)
            .order_by(desc(EmailAnalysisEvent.created_at))
            .limit(min(limit, 200))
        ).all()
        return [
            {
                "id": row.id,
                "created_at": row.created_at.isoformat(),
                "risk_score": row.risk_score,
                "classification": row.classification,
                "domain": row.domain,
            }
            for row in reversed(rows)
        ]

    def create_feedback(self, feedback: dict[str, Any]) -> FeedbackEvent:
        existing = self.db.scalar(
            select(FeedbackEvent)
            .where(FeedbackEvent.sample_hash == feedback["sample_hash"])
            .where(FeedbackEvent.user_feedback == feedback["user_feedback"])
            .order_by(desc(FeedbackEvent.created_at))
        )
        if existing:
            return existing

        record = FeedbackEvent(
            sample_hash=feedback["sample_hash"],
            domain=feedback.get("domain", ""),
            source=feedback.get("source", "extension"),
            current_risk_score=float(feedback.get("current_risk_score", 0.0)),
            current_classification=feedback.get("current_classification", "unknown"),
            user_feedback=feedback["user_feedback"],
            review_status="pending",
            reasons_json=json.dumps(feedback.get("reasons", [])),
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def recent_feedback(self, limit: int = 50) -> list[dict[str, Any]]:
        rows = self.db.scalars(
            select(FeedbackEvent)
            .order_by(desc(FeedbackEvent.created_at))
            .limit(min(limit, 200))
        ).all()
        return [self._serialize_feedback(row) for row in rows]

    def _serialize(self, row: EmailAnalysisEvent) -> dict[str, Any]:
        return {
            "id": row.id,
            "sample_hash": row.sample_hash,
            "sender_hash": row.sender_hash,
            "subject_hash": row.subject_hash,
            "domain": row.domain,
            "source": row.source,
            "risk_score": row.risk_score,
            "classification": row.classification,
            "confidence": row.confidence,
            "impersonated_brand": row.impersonated_brand,
            "reasons": json.loads(row.reasons_json or "[]"),
            "created_at": row.created_at.isoformat(),
        }

    def _serialize_feedback(self, row: FeedbackEvent) -> dict[str, Any]:
        return {
            "id": row.id,
            "sample_hash": row.sample_hash,
            "domain": row.domain,
            "source": row.source,
            "current_risk_score": row.current_risk_score,
            "current_classification": row.current_classification,
            "user_feedback": row.user_feedback,
            "review_status": row.review_status,
            "reasons": json.loads(row.reasons_json or "[]"),
            "created_at": row.created_at.isoformat(),
        }

    def _to_siem(self, row: EmailAnalysisEvent) -> dict[str, Any]:
        return {
            "event.kind": "alert" if row.classification != "safe" else "event",
            "event.category": ["email", "threat"],
            "event.type": ["indicator"],
            "event.module": "phishguard",
            "event.created": row.created_at.isoformat(),
            "threat.indicator.type": "email",
            "threat.indicator.confidence": row.confidence,
            "phishguard.sample_hash": row.sample_hash,
            "phishguard.sender_hash": row.sender_hash,
            "phishguard.subject_hash": row.subject_hash,
            "phishguard.domain": row.domain,
            "phishguard.risk_score": row.risk_score,
            "phishguard.classification": row.classification,
            "phishguard.impersonated_brand": row.impersonated_brand,
            "phishguard.reasons": json.loads(row.reasons_json or "[]"),
        }
