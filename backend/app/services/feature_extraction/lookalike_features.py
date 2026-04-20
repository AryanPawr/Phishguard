from __future__ import annotations

import re
import unicodedata
from urllib.parse import urlparse

from app.intelligence.domain_trust import trust_record_for_domain
from app.intelligence.spoof_patterns import SPOOFING_TERMS
from app.intelligence.verified_domains import VERIFIED_DOMAINS


CONFUSABLES = {
    "а": "a",
    "ɑ": "a",
    "е": "e",
    "ο": "o",
    "о": "o",
    "р": "p",
    "с": "c",
    "х": "x",
    "і": "i",
    "Ι": "l",
    "ӏ": "l",
    "ɢ": "g",
    "0": "o",
    "1": "l",
    "3": "e",
    "5": "s",
    "rn": "m",
    "vv": "w",
}

GENERIC_SHORTENERS = {
    "bit.ly",
    "tinyurl.com",
    "shorturl.at",
    "rebrand.ly",
    "cutt.ly",
    "is.gd",
    "buff.ly",
    "ow.ly",
    "t.ly",
    "s.id",
}

DEFANGED_DOT_RE = re.compile(r"\[\s*\.\s*\]|\(\s*\.\s*\)|\{\s*\.\s*\}", re.IGNORECASE)
DOMAIN_RE = re.compile(r"\b(?:[a-z0-9-]+\.)+[a-z]{2,}\b", re.IGNORECASE)


def normalize_defanged_url(value: str | None) -> str:
    text = value or ""
    text = re.sub(r"\bhxxps://", "https://", text, flags=re.IGNORECASE)
    text = re.sub(r"\bhxxp://", "http://", text, flags=re.IGNORECASE)
    return DEFANGED_DOT_RE.sub(".", text)


def host_from_url(value: str | None) -> str:
    normalized = normalize_defanged_url(value)
    parsed = urlparse(normalized if "://" in normalized else f"https://{normalized}")
    return (parsed.hostname or "").lower().strip(".")


def labels(domain: str) -> list[str]:
    return [part for part in domain.lower().strip(".").split(".") if part]


def root_label(domain: str) -> str:
    parts = labels(domain)
    return parts[0] if parts else ""


def verified_domain_set() -> set[str]:
    values: set[str] = set()
    for domains in VERIFIED_DOMAINS.values():
        values.update(domain.lower() for domain in domains)
    return values


def brand_label_map() -> dict[str, str]:
    mapping: dict[str, str] = {}
    for brand, domains in VERIFIED_DOMAINS.items():
        for domain in domains:
            label = root_label(domain)
            if len(label) >= 3:
                mapping[label] = brand
    return mapping


def is_verified_for_brand(host: str, brand: str) -> bool:
    return any(
        host == domain or host.endswith(f".{domain}")
        for domain in VERIFIED_DOMAINS.get(brand, set())
    )


def script_bucket(char: str) -> str:
    if char.isascii():
        return "latin"
    name = unicodedata.name(char, "")
    if "CYRILLIC" in name:
        return "cyrillic"
    if "GREEK" in name:
        return "greek"
    if "LATIN" in name:
        return "latin"
    return "other"


def has_mixed_scripts(value: str) -> bool:
    scripts = {script_bucket(char) for char in value if char.isalpha()}
    return len(scripts) > 1


def confusable_skeleton(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value)
    for source, replacement in CONFUSABLES.items():
        normalized = normalized.replace(source, replacement)
    return normalized.lower()


def edit_distance(left: str, right: str) -> int:
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
            current.append(
                min(
                    previous[index_right] + 1,
                    current[index_right - 1] + 1,
                    previous[index_right - 1] + (char_left != char_right),
                )
            )
        previous = current
    return previous[-1]


def brand_in_subdomain(host: str) -> str | None:
    if trust_record_for_domain(host):
        return None
    normalized = host.lower()
    for verified in verified_domain_set():
        if normalized.startswith(f"{verified}.") or f".{verified}." in normalized:
            for brand, domains in VERIFIED_DOMAINS.items():
                if verified in domains:
                    return brand
    return None


def embedded_brand_label(host: str) -> str | None:
    if trust_record_for_domain(host):
        return None
    host_labels = labels(host)
    if not host_labels:
        return None
    candidate_labels = host_labels[:-2] if len(host_labels) > 2 else [host_labels[0]]
    for brand_label, brand in brand_label_map().items():
        if len(brand_label) < 5:
            continue
        if any(brand_label in label and label != brand_label for label in candidate_labels):
            return brand
    return None


def brand_in_path(url: str) -> str | None:
    host = host_from_url(url)
    if trust_record_for_domain(host):
        return None
    normalized = normalize_defanged_url(url).lower()
    parsed = urlparse(normalized if "://" in normalized else f"https://{normalized}")
    path = parsed.path.lower()
    for verified in verified_domain_set():
        if verified in path:
            for brand, domains in VERIFIED_DOMAINS.items():
                if verified in domains:
                    return brand
    return None


def find_defanged_domains(text: str | None) -> list[str]:
    normalized = normalize_defanged_url(text)
    return DOMAIN_RE.findall(normalized)


def analyze_domain_lookalike(domain: str | None) -> dict[str, float | str | None]:
    host = (domain or "").lower().strip(".")
    if not host:
        return {
            "lookalike_score": 0.0,
            "homograph_flag": 0.0,
            "mixed_script_flag": 0.0,
            "typosquat_flag": 0.0,
            "brand_in_subdomain_flag": 0.0,
            "suspicious_hyphenated_brand_flag": 0.0,
            "lookalike_brand": None,
        }

    label = root_label(host)
    skeleton = confusable_skeleton(label)
    brand_map = brand_label_map()
    best_brand: str | None = None
    best_distance = 999
    for brand_label, brand in brand_map.items():
        distance = edit_distance(skeleton, brand_label)
        if distance < best_distance:
            best_distance = distance
            best_brand = brand

    non_ascii = any(not char.isascii() for char in host)
    mixed_script = has_mixed_scripts(host)
    homograph = bool(non_ascii and best_distance <= 1 and best_brand and not is_verified_for_brand(host, best_brand))
    typosquat = bool(
        best_brand
        and not is_verified_for_brand(host, best_brand)
        and len(label) >= 5
        and 0 < best_distance <= (2 if len(label) >= 8 else 1)
    )
    subdomain_brand = brand_in_subdomain(host)
    embedded_brand = embedded_brand_label(host)
    hyphen_brand = bool(
        "-" in host
        and not trust_record_for_domain(host)
        and (
            bool(embedded_brand)
            or bool(best_brand and not is_verified_for_brand(host, best_brand) and any(term in host for term in SPOOFING_TERMS))
        )
    )

    score = 0.0
    if homograph:
        score += 0.45
    if mixed_script:
        score += 0.20
    if typosquat:
        score += 0.35
    if subdomain_brand:
        score += 0.45
        best_brand = subdomain_brand
    if embedded_brand:
        score += 0.30
        best_brand = embedded_brand
    if hyphen_brand:
        score += 0.25
    if "xn--" in host:
        score += 0.30

    return {
        "lookalike_score": round(min(score, 1.0), 4),
        "homograph_flag": 1.0 if homograph else 0.0,
        "mixed_script_flag": 1.0 if mixed_script else 0.0,
        "typosquat_flag": 1.0 if typosquat else 0.0,
        "brand_in_subdomain_flag": 1.0 if subdomain_brand or embedded_brand else 0.0,
        "suspicious_hyphenated_brand_flag": 1.0 if hyphen_brand else 0.0,
        "lookalike_brand": best_brand if score > 0 else None,
    }


def analyze_url_lookalike(url: str | None) -> dict[str, float | str | None]:
    host = host_from_url(url)
    domain_result = analyze_domain_lookalike(host)
    path_brand = brand_in_path(url or "")
    shortener = host in GENERIC_SHORTENERS
    score = float(domain_result["lookalike_score"])
    if path_brand:
        score += 0.35
    if shortener:
        score += 0.20
    return {
        "url_lookalike_score": round(min(score, 1.0), 4),
        "url_brand_in_path_flag": 1.0 if path_brand else 0.0,
        "generic_shortener_flag": 1.0 if shortener else 0.0,
        "url_lookalike_brand": domain_result.get("lookalike_brand") or path_brand,
    }
