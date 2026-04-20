from __future__ import annotations

import math
import re
from urllib.parse import urlparse

from app.intelligence.brand_registry import BRANDS, Brand, brand_for_verified_domain, find_brand_mentions
from app.intelligence.domain_trust import trust_record_for_domain
from app.services.feature_extraction.lookalike_features import analyze_domain_lookalike


DOMAIN_RE = re.compile(r"@([A-Za-z0-9.-]+\.[A-Za-z]{2,})")
SUSPICIOUS_DELEGATED_SUFFIXES = {
    "uk.net",
    "gb.net",
    "co.com",
    "eu.com",
    "us.com",
    "za.com",
    "jpn.com",
    "br.com",
    "cn.com",
}
HIGH_RISK_INFRA_TERMS = {
    "cdn",
    "cloud",
    "fusion",
    "mail",
    "relay",
    "rift",
    "smtp",
    "track",
}


def normalize_domain(domain: str | None) -> str:
    value = (domain or "").lower().strip()
    if "://" in value:
        value = urlparse(value).hostname or ""
    if "@" in value:
        match = DOMAIN_RE.search(value)
        value = match.group(1) if match else value.rsplit("@", 1)[-1]
    return value.removeprefix("www.").strip(".")


def levenshtein(left: str, right: str) -> int:
    if left == right:
        return 0
    if not left:
        return len(right)
    if not right:
        return len(left)

    previous = list(range(len(right) + 1))
    for index_left, char_left in enumerate(left, start=1):
        current = [index_left]
        for index_right, char_right in enumerate(right, start=1):
            insertions = previous[index_right] + 1
            deletions = current[index_right - 1] + 1
            substitutions = previous[index_right - 1] + (char_left != char_right)
            current.append(min(insertions, deletions, substitutions))
        previous = current
    return previous[-1]


def subdomain_depth(domain: str) -> int:
    parts = [part for part in domain.split(".") if part]
    return max(len(parts) - 2, 0)


def shannon_entropy(value: str) -> float:
    if not value:
        return 0.0
    length = len(value)
    return -sum((value.count(char) / length) * math.log2(value.count(char) / length) for char in set(value))


def domain_labels(domain: str) -> list[str]:
    return [part for part in domain.split(".") if part]


def suspicious_delegated_suffix(domain: str) -> bool:
    return any(domain == suffix or domain.endswith(f".{suffix}") for suffix in SUSPICIOUS_DELEGATED_SUFFIXES)


def random_label_score(label: str) -> float:
    normalized = re.sub(r"[^a-z0-9]", "", label.lower())
    if len(normalized) < 7:
        return 0.0

    entropy = shannon_entropy(normalized)
    digit_ratio = sum(char.isdigit() for char in normalized) / len(normalized)
    rare_ratio = sum(char in "jqxz" for char in normalized) / len(normalized)
    vowel_ratio = sum(char in "aeiou" for char in normalized) / len(normalized)
    consonant_runs = re.findall(r"[bcdfghjklmnpqrstvwxyz]{4,}", normalized)

    score = 0.0
    if entropy >= 2.75:
        score += 0.45
    if rare_ratio >= 0.18:
        score += 0.18
    if digit_ratio >= 0.25:
        score += 0.18
    if vowel_ratio <= 0.22:
        score += 0.12
    if consonant_runs:
        score += 0.12
    return round(min(score, 1.0), 4)


def infrastructure_score(domain: str) -> dict[str, float | str]:
    labels = domain_labels(domain)
    if not labels:
        return {
            "sender_domain_entropy": 0.0,
            "random_label_score": 0.0,
            "random_subdomain_flag": 0.0,
            "suspicious_delegated_suffix_flag": 0.0,
            "domain_infrastructure_score": 0.0,
            "highest_entropy_label": "",
        }

    candidate_labels = labels[:-2] if len(labels) > 2 else []
    label_scores = [(label, random_label_score(label), shannon_entropy(label)) for label in candidate_labels]
    highest = max(label_scores, key=lambda item: item[1], default=("", 0.0, 0.0))
    delegated_suffix = suspicious_delegated_suffix(domain)
    infra_terms = sum(1 for term in HIGH_RISK_INFRA_TERMS if term in domain)

    score = 0.0
    score += highest[1] * 0.50
    if highest[1] >= 0.45:
        score += 0.20
    if delegated_suffix:
        score += 0.25
    if subdomain_depth(domain) >= 2:
        score += 0.12
    if infra_terms >= 2:
        score += 0.08

    return {
        "sender_domain_entropy": round(shannon_entropy(domain.replace(".", "")), 4),
        "random_label_score": round(highest[1], 4),
        "random_subdomain_flag": 1.0 if highest[1] >= 0.45 else 0.0,
        "suspicious_delegated_suffix_flag": 1.0 if delegated_suffix else 0.0,
        "domain_infrastructure_score": round(min(score, 1.0), 4),
        "highest_entropy_label": highest[0],
    }


def min_brand_distance(domain: str) -> tuple[float, Brand | None]:
    compact = domain.split(".")[0].replace("-", "")
    best_distance = 999
    best_brand: Brand | None = None
    for brand in BRANDS:
        candidates = {brand.name.lower().replace(" ", ""), *brand.aliases}
        for candidate in candidates:
            distance = levenshtein(compact, candidate)
            if distance < best_distance:
                best_distance = distance
                best_brand = brand
    normalized = best_distance / max(len(compact), 1)
    return round(normalized, 4), best_brand


def extract_domain_features(
    domain: str | None,
    sender_email: str | None,
    display_name: str | None,
    subject: str | None = None,
) -> dict[str, float | str | None]:
    normalized_domain = normalize_domain(domain or sender_email)
    verified_brand = brand_for_verified_domain(normalized_domain)
    mentioned = find_brand_mentions(" ".join([display_name or "", subject or ""]))
    distance, closest_brand = min_brand_distance(normalized_domain) if normalized_domain else (1.0, None)
    close_lookalike_brand = closest_brand if distance <= 0.34 else None
    likely_brand = verified_brand or (mentioned[0] if mentioned else close_lookalike_brand)
    display_name_mismatch = bool(mentioned and not verified_brand)
    brand_registry_mismatch = bool(close_lookalike_brand and not verified_brand)
    infra = infrastructure_score(normalized_domain)
    trust_record = trust_record_for_domain(normalized_domain)
    lookalike = analyze_domain_lookalike(normalized_domain)
    if lookalike.get("lookalike_brand") and not likely_brand:
        likely_brand = next((brand for brand in BRANDS if brand.name == lookalike["lookalike_brand"]), likely_brand)

    return {
        "normalized_domain": normalized_domain,
        "recognized_brand": verified_brand.name if verified_brand else None,
        "domain_trust_type": trust_record.trust_type if trust_record else None,
        "punycode_detection": 1.0 if "xn--" in normalized_domain else 0.0,
        "subdomain_depth": float(subdomain_depth(normalized_domain)),
        "levenshtein_distance_to_brand": float(distance),
        "display_name_mismatch": 1.0 if display_name_mismatch else 0.0,
        "domain_registry_mismatch": 1.0 if brand_registry_mismatch else 0.0,
        "likely_brand": likely_brand.name if likely_brand else None,
        **infra,
        **lookalike,
    }
