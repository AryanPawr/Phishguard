from __future__ import annotations

from typing import Any

from app.intelligence.brand_registry import brand_for_verified_domain, find_brand_mentions
from app.intelligence.spoof_patterns import HOMOGLYPH_HINTS, SPOOFING_TERMS
from app.services.feature_extraction.domain_features import normalize_domain


def contains_homoglyph(value: str) -> bool:
    return any(char in HOMOGLYPH_HINTS for char in value)


class ImpersonationDetector:
    def evaluate(self, payload: dict[str, Any], features: dict[str, Any]) -> dict[str, Any]:
        domain = normalize_domain(payload.get("domain") or payload.get("sender_email"))
        verified_brand = brand_for_verified_domain(domain)
        detected_brand: str | None = None
        mentioned_brands = find_brand_mentions(
            " ".join(
                [
                    str(payload.get("display_name", "")),
                    str(payload.get("subject", "")),
                    domain,
                ]
            )
        )
        reasons: list[str] = []
        score = 0.0

        if mentioned_brands and not verified_brand:
            score += 0.34
            detected_brand = mentioned_brands[0].name
            reasons.append("Brand is mentioned from a non-verified sender domain")
        if float(features.get("display_name_mismatch", 0)) > 0:
            score += 0.18
            detected_brand = detected_brand or (mentioned_brands[0].name if mentioned_brands else None)
            reasons.append("Display name references a known brand but the domain does not match")
        if float(features.get("domain_registry_mismatch", 0)) > 0:
            score += 0.22
            detected_brand = detected_brand or str(features.get("likely_brand") or "")
            reasons.append("Sender domain resembles a known brand outside the verified registry")
        if contains_homoglyph(domain):
            score += 0.16
            reasons.append("Domain contains homoglyph characters")
        if any(term in domain for term in SPOOFING_TERMS):
            score += 0.10
            reasons.append("Domain includes common spoofing terms")

        if verified_brand:
            score = max(score - 0.22, 0.0)
            detected_brand = None

        return {
            "score": round(min(score, 1.0), 4),
            "brand": detected_brand or None,
            "reasons": reasons,
        }
