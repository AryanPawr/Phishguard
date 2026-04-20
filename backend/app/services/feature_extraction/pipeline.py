from __future__ import annotations

from typing import Any

from app.services.feature_extraction.domain_features import extract_domain_features
from app.services.feature_extraction.link_features import extract_link_features
from app.services.feature_extraction.structural_features import extract_structural_features
from app.services.feature_extraction.text_features import extract_text_features


def extract_features(payload: dict[str, Any]) -> dict[str, Any]:
    text_features = extract_text_features(payload.get("subject"), payload.get("body_text"))
    link_features = extract_link_features(payload.get("links", []))
    domain_features = extract_domain_features(
        payload.get("domain"),
        payload.get("sender_email"),
        payload.get("display_name"),
        payload.get("subject"),
    )
    structural_features = extract_structural_features(payload.get("html"), payload.get("body_text"))
    return {
        **text_features,
        **link_features,
        **domain_features,
        **structural_features,
    }
