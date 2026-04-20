from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.core.security import canonical_hash, hmac_hash, mask_payload
from app.database.repository import EventRepository
from app.database.session import get_db
from app.services.feature_extraction import extract_features
from app.services.impersonation_detector import ImpersonationDetector
from app.services.ml_engine import get_model
from app.services.reputation_service import ReputationService
from app.services.scoring_engine import ScoringEngine

router = APIRouter(prefix="/analyze", tags=["analysis"])


class EmailLink(BaseModel):
    href: str = Field(..., max_length=2048)
    anchor_text: str = Field(default="", max_length=512)


class AnalyzeRequest(BaseModel):
    sender_email: str = Field(default="", max_length=320)
    display_name: str = Field(default="", max_length=256)
    subject: str = Field(default="", max_length=512)
    body_text: str = Field(default="", max_length=50000)
    html: str | None = Field(default=None, max_length=120000)
    links: list[EmailLink] = Field(default_factory=list, max_length=200)
    domain: str = Field(default="", max_length=255)
    heuristic_score: float = Field(default=0.0, ge=0.0, le=1.0)
    sender_local_category: Literal["noreply", "notification", "support", "unknown"] = "unknown"
    client_reasons: list[str] = Field(default_factory=list, max_length=25)
    source: Literal["gmail", "outlook", "generic", "api"] = "generic"

    @field_validator("client_reasons")
    @classmethod
    def clamp_reasons(cls, values: list[str]) -> list[str]:
        return [str(value)[:240] for value in values[:25]]


class AnalyzeResponse(BaseModel):
    risk_score: float
    classification: Literal["safe", "suspicious", "phishing"]
    confidence: Literal["low", "medium", "high"]
    reasons: list[str]
    model_version: str
    sample_hash: str
    domain: str
    source: str
    impersonated_brand: str | None = None
    components: dict[str, float]


@router.post("", response_model=AnalyzeResponse)
def analyze_email(payload: AnalyzeRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
    raw_payload = payload.model_dump()
    sample_hash = canonical_hash(
        {
            "sender_email": raw_payload.get("sender_email"),
            "subject": raw_payload.get("subject"),
            "body_text": raw_payload.get("body_text"),
            "links": raw_payload.get("links"),
        }
    )
    masked_payload = mask_payload(raw_payload)
    features = extract_features(masked_payload)

    model = get_model()
    ml_probability = model.predict_probability(features)
    impersonation = ImpersonationDetector().evaluate(masked_payload, features)
    reputation = ReputationService().evaluate(masked_payload, features)
    domain_registry_mismatch = float(features.get("domain_registry_mismatch", 0.0) or 0.0)
    heuristic_score = float(masked_payload.get("heuristic_score", 0.0) or 0.0)

    reasons = [
        *masked_payload.get("client_reasons", []),
        *impersonation["reasons"],
        *reputation["reasons"],
    ]
    if ml_probability >= 0.7:
        reasons.append("ML baseline assigned high phishing probability")
    if float(features.get("credential_phrase_count", 0)) > 0:
        reasons.append("Message contains credential harvesting language")
    if float(features.get("promotional_spam_score", 0)) >= 0.45:
        reasons.append("Message contains gambling or prize-lure spam language")
    if float(features.get("defanged_url_count", 0)) > 0:
        reasons.append("Message contains defanged URL indicators")
    if (
        float(features.get("urgency_keyword_count", 0)) > 0
        and (
            float(features.get("lookalike_score", 0)) >= 0.35
            or float(features.get("url_lookalike_score", 0)) >= 0.35
        )
    ):
        reasons.append("Message combines urgent language with lookalike URL indicators")
    if float(features.get("anchor_mismatch_flag", 0)) > 0:
        reasons.append("One or more links use mismatched anchor text")

    result = ScoringEngine().score(
        ml_probability=ml_probability,
        impersonation_score=float(impersonation["score"]),
        heuristic_score=heuristic_score,
        link_reputation=float(reputation["score"]),
        domain_registry_mismatch=domain_registry_mismatch,
        trusted_sender=bool(features.get("recognized_brand")),
        sender_local_category=str(masked_payload.get("sender_local_category", "unknown")),
        reasons=reasons,
    )

    EventRepository(db).create_event(
        {
            "sample_hash": sample_hash,
            "sender_hash": hmac_hash(raw_payload.get("sender_email", "")),
            "subject_hash": hmac_hash(raw_payload.get("subject", "")),
            "domain": features.get("normalized_domain", ""),
            "source": masked_payload.get("source", "generic"),
            "risk_score": result["risk_score"],
            "classification": result["classification"],
            "confidence": result["confidence"],
            "impersonated_brand": impersonation.get("brand"),
            "reasons": result["reasons"],
            "features": {
                key: value
                for key, value in features.items()
                if key not in {"body_text"}
            },
        }
    )

    return {
        **result,
        "model_version": model.version,
        "sample_hash": sample_hash,
        "domain": str(features.get("normalized_domain", "")),
        "source": str(masked_payload.get("source", "generic")),
        "impersonated_brand": impersonation.get("brand"),
        "components": {
            "ml_probability": ml_probability,
            "impersonation_score": float(impersonation["score"]),
            "heuristic_score": heuristic_score,
            "link_reputation": float(reputation["score"]),
            "domain_registry_mismatch": domain_registry_mismatch,
        },
    }
