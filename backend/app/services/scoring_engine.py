from __future__ import annotations

from typing import Any


class ScoringEngine:
    def score(
        self,
        *,
        ml_probability: float,
        impersonation_score: float,
        heuristic_score: float,
        link_reputation: float,
        domain_registry_mismatch: float,
        reasons: list[str],
        trusted_sender: bool = False,
        sender_local_category: str = "unknown",
    ) -> dict[str, Any]:
        risk_score = (
            0.30 * ml_probability
            + 0.25 * impersonation_score
            + 0.20 * heuristic_score
            + 0.15 * link_reputation
            + 0.10 * domain_registry_mismatch
        )
        if link_reputation >= 0.90:
            risk_score = max(risk_score, 0.34)
        elif link_reputation >= 0.65:
            risk_score = max(risk_score, 0.32)
        if any("gambling or prize-lure spam" in reason for reason in reasons):
            risk_score = max(risk_score, 0.34)
        if any("lookalike" in reason.lower() or "look-alike" in reason.lower() for reason in reasons):
            risk_score = max(risk_score, 0.38)
        if trusted_sender and sender_local_category in {"noreply", "notification"}:
            risk_score = max(risk_score - 0.04, 0.0)
        risk_score = round(min(max(risk_score, 0.0), 1.0), 4)

        if risk_score >= 0.72:
            classification = "phishing"
        elif risk_score >= 0.32:
            classification = "suspicious"
        else:
            classification = "safe"

        confidence = "low"
        if risk_score >= 0.78 or risk_score <= 0.15:
            confidence = "high"
        elif risk_score >= 0.52 or risk_score <= 0.26:
            confidence = "medium"

        return {
            "risk_score": risk_score,
            "classification": classification,
            "confidence": confidence,
            "reasons": sorted(set(reason for reason in reasons if reason)),
        }
