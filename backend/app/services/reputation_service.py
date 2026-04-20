from __future__ import annotations

from typing import Any

from app.intelligence.spoof_patterns import SUSPICIOUS_TLDS
from app.intelligence.domain_trust import is_strong_sender_domain, trust_record_for_domain
from app.services.feature_extraction.domain_features import infrastructure_score, normalize_domain
from app.services.feature_extraction.link_features import host_from_url, is_ip_host
from app.services.feature_extraction.lookalike_features import analyze_domain_lookalike, analyze_url_lookalike


LOCAL_BLOCKLIST = {
    "paypal-security-login.example",
    "office365-password-reset.example",
    "secure-bank-verify.example",
}


class ReputationService:
    def evaluate(self, payload: dict[str, Any], features: dict[str, Any]) -> dict[str, Any]:
        link_result = self.evaluate_links(payload.get("links", []))
        domain_result = self.evaluate_domain(
            str(features.get("normalized_domain") or payload.get("domain") or payload.get("sender_email") or "")
        )
        score = max(float(link_result["score"]), float(domain_result["score"]))
        reasons = sorted(set([*link_result["reasons"], *domain_result["reasons"]]))
        return {"score": round(score, 4), "reasons": reasons}

    def evaluate_links(self, links: list[dict[str, Any]]) -> dict[str, Any]:
        if not links:
            return {"score": 0.0, "reasons": []}
        reasons: list[str] = []
        score = 0.0
        for link in links:
            href = str(link.get("href", ""))
            host = host_from_url(href)
            tld = host.split(".")[-1] if "." in host else ""
            trust_record = trust_record_for_domain(host)
            url_lookalike_score = float(link.get("url_lookalike_score", 0) or 0)
            if host in LOCAL_BLOCKLIST:
                score += 0.45
                reasons.append("URL matched local threat intelligence blocklist")
            if is_ip_host(host):
                score += 0.22
                reasons.append("URL uses an IP address instead of a domain")
            if tld in SUSPICIOUS_TLDS:
                score += 0.12
                reasons.append(f"URL uses suspicious TLD .{tld}")
            if href.count("%") > 4 and not trust_record:
                score += 0.08
                reasons.append("URL contains heavy percent encoding")
            lookalike = analyze_url_lookalike(href)
            url_lookalike_score = max(url_lookalike_score, float(lookalike["url_lookalike_score"]))
            if float(lookalike["url_brand_in_path_flag"]) > 0:
                score += 0.26
                reasons.append("URL path contains a trusted brand domain while the real destination is unrelated")
            if float(lookalike["generic_shortener_flag"]) > 0:
                score += 0.12
                reasons.append("URL uses a generic shortener that hides the final destination")
            if url_lookalike_score >= 0.35:
                score += min(url_lookalike_score, 0.45)
                reasons.append("URL contains lookalike brand or homograph indicators")
        return {"score": round(min(score, 1.0), 4), "reasons": sorted(set(reasons))}

    def evaluate_domain(self, domain: str) -> dict[str, Any]:
        normalized = normalize_domain(domain)
        if not normalized:
            return {"score": 0.0, "reasons": []}
        if is_strong_sender_domain(normalized):
            return {"score": 0.0, "reasons": []}

        infra = infrastructure_score(normalized)
        score = float(infra["domain_infrastructure_score"])
        reasons: list[str] = []
        if float(infra["random_subdomain_flag"]) > 0:
            reasons.append("Sender domain contains a random-looking high-entropy label")
        if float(infra["suspicious_delegated_suffix_flag"]) > 0:
            reasons.append("Sender domain uses a delegated suffix often abused for disposable infrastructure")
        if float(infra["random_label_score"]) >= 0.6:
            reasons.append("Sender infrastructure resembles machine-generated spam infrastructure")
        lookalike = analyze_domain_lookalike(normalized)
        lookalike_score = float(lookalike["lookalike_score"])
        if float(lookalike["homograph_flag"]) > 0:
            reasons.append("Sender domain contains look-alike Unicode characters")
        if float(lookalike["mixed_script_flag"]) > 0:
            reasons.append("Sender domain uses mixed-script characters that resemble a trusted brand")
        if float(lookalike["typosquat_flag"]) > 0:
            reasons.append("Sender domain is a close misspelling of a known brand")
        if float(lookalike["brand_in_subdomain_flag"]) > 0:
            reasons.append("Sender domain places a trusted brand name in the subdomain while the actual domain is different")
        if float(lookalike["suspicious_hyphenated_brand_flag"]) > 0:
            reasons.append("Sender domain combines brand terms with account or security update language")
        score = max(score, lookalike_score)
        return {"score": round(min(score, 1.0), 4), "reasons": reasons}
