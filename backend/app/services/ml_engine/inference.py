from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import pandas as pd


MODEL_VERSION = "structured-logreg-v1"

NUMERIC_FEATURE_COLUMNS = [
    "word_count",
    "unique_word_ratio",
    "uppercase_ratio",
    "exclamation_count",
    "urgency_keyword_count",
    "credential_phrase_count",
    "high_risk_phrase_count",
    "spam_lure_keyword_count",
    "gambling_keyword_count",
    "hindi_spam_lure_count",
    "emoji_count",
    "defanged_url_count",
    "promotional_spam_score",
    "url_count",
    "anchor_mismatch_flag",
    "anchor_mismatch_count",
    "url_entropy_avg",
    "url_entropy_max",
    "ip_based_url_flag",
    "suspicious_tld_score",
    "encoded_character_count",
    "punycode_detection",
    "subdomain_depth",
    "levenshtein_distance_to_brand",
    "display_name_mismatch",
    "domain_registry_mismatch",
    "sender_domain_entropy",
    "random_label_score",
    "random_subdomain_flag",
    "suspicious_delegated_suffix_flag",
    "domain_infrastructure_score",
    "lookalike_score",
    "homograph_flag",
    "mixed_script_flag",
    "typosquat_flag",
    "brand_in_subdomain_flag",
    "suspicious_hyphenated_brand_flag",
    "url_lookalike_score",
    "url_brand_in_path_flag",
    "generic_shortener_flag",
    "html_to_text_ratio",
    "form_tag_presence",
    "hidden_element_count",
]


class PhishingModel:
    def __init__(self, model_path: Path):
        self.model_path = Path(model_path)
        self.pipeline: Any | None = None
        self.version = "heuristic-fallback"
        self.load()

    def load(self) -> None:
        if not self.model_path.exists() or self.model_path.stat().st_size == 0:
            return
        try:
            artifact = joblib.load(self.model_path)
        except Exception:
            return

        if isinstance(artifact, dict):
            self.pipeline = artifact.get("pipeline")
            self.version = artifact.get("version", MODEL_VERSION)
        else:
            self.pipeline = artifact
            self.version = MODEL_VERSION

    def predict_probability(self, features: dict[str, Any]) -> float:
        if self.pipeline is not None:
            frame = feature_frame(features)
            probability = self.pipeline.predict_proba(frame)[0][1]
            return round(float(probability), 4)
        return round(self._fallback_probability(features), 4)

    def _fallback_probability(self, features: dict[str, Any]) -> float:
        score = 0.0
        score += min(float(features.get("urgency_keyword_count", 0)) / 4, 1) * 0.14
        score += min(float(features.get("credential_phrase_count", 0)) / 2, 1) * 0.16
        score += min(float(features.get("promotional_spam_score", 0)), 1) * 0.14
        score += float(features.get("anchor_mismatch_flag", 0)) * 0.14
        score += float(features.get("ip_based_url_flag", 0)) * 0.10
        score += min(float(features.get("suspicious_tld_score", 0)), 1) * 0.10
        score += float(features.get("punycode_detection", 0)) * 0.12
        score += float(features.get("display_name_mismatch", 0)) * 0.08
        score += float(features.get("domain_registry_mismatch", 0)) * 0.12
        score += min(float(features.get("domain_infrastructure_score", 0)), 1) * 0.16
        score += min(float(features.get("lookalike_score", 0)), 1) * 0.18
        score += min(float(features.get("url_lookalike_score", 0)), 1) * 0.16
        score += min(float(features.get("hidden_element_count", 0)) / 3, 1) * 0.08
        return min(max(score, 0.02), 0.98)


def feature_frame(features: dict[str, Any]) -> pd.DataFrame:
    row = {
        "body_text": str(features.get("body_text", "")),
        **{column: float(features.get(column, 0.0) or 0.0) for column in NUMERIC_FEATURE_COLUMNS},
    }
    return pd.DataFrame([row])
