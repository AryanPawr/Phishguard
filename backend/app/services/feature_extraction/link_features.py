from __future__ import annotations

import ipaddress
import math
import re
from urllib.parse import unquote, urlparse

from app.intelligence.spoof_patterns import SUSPICIOUS_TLDS
from app.services.feature_extraction.lookalike_features import analyze_url_lookalike

DOMAIN_IN_TEXT_RE = re.compile(r"\b(?:[a-z0-9-]+\.)+[a-z]{2,}\b", re.IGNORECASE)


def shannon_entropy(value: str) -> float:
    if not value:
        return 0.0
    frequencies = {char: value.count(char) for char in set(value)}
    length = len(value)
    return -sum((count / length) * math.log2(count / length) for count in frequencies.values())


def host_from_url(url: str) -> str:
    parsed = urlparse(url if "://" in url else f"https://{url}")
    return (parsed.hostname or "").lower().strip(".")


def is_ip_host(host: str) -> bool:
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        return False


def registered_domain_like(host: str) -> str:
    parts = [part for part in host.split(".") if part]
    if len(parts) <= 2:
        return host
    return ".".join(parts[-2:])


def anchor_domain_mismatch(anchor_text: str, href: str) -> bool:
    anchor_domains = DOMAIN_IN_TEXT_RE.findall(anchor_text or "")
    if not anchor_domains:
        return False
    href_domain = registered_domain_like(host_from_url(href))
    return all(registered_domain_like(domain.lower()) != href_domain for domain in anchor_domains)


def encoded_character_count(url: str) -> int:
    decoded = unquote(url or "")
    return max(len(url or "") - len(decoded), 0) + (url or "").count("%")


def extract_link_features(links: list[dict[str, str]]) -> dict[str, float]:
    urls = [str(link.get("href", "")) for link in links if link.get("href")]
    hosts = [host_from_url(url) for url in urls]
    entropies = [shannon_entropy(url) for url in urls]
    mismatch_count = sum(
        1
        for link in links
        if anchor_domain_mismatch(str(link.get("anchor_text", "")), str(link.get("href", "")))
    )
    suspicious_tld_count = sum(
        1
        for host in hosts
        if host.split(".")[-1].lower() in SUSPICIOUS_TLDS
    )
    encoded_count = sum(encoded_character_count(url) for url in urls)
    ip_count = sum(1 for host in hosts if is_ip_host(host))
    lookalike_results = [analyze_url_lookalike(url) for url in urls]
    url_lookalike_score = max(
        [float(result["url_lookalike_score"]) for result in lookalike_results] or [0.0]
    )
    brand_in_path_count = sum(float(result["url_brand_in_path_flag"]) for result in lookalike_results)
    shortener_count = sum(float(result["generic_shortener_flag"]) for result in lookalike_results)

    return {
        "url_count": float(len(urls)),
        "anchor_mismatch_flag": 1.0 if mismatch_count else 0.0,
        "anchor_mismatch_count": float(mismatch_count),
        "url_entropy_avg": round(sum(entropies) / max(len(entropies), 1), 4),
        "url_entropy_max": round(max(entropies or [0.0]), 4),
        "ip_based_url_flag": 1.0 if ip_count else 0.0,
        "suspicious_tld_score": round(suspicious_tld_count / max(len(urls), 1), 4),
        "encoded_character_count": float(encoded_count),
        "url_lookalike_score": round(url_lookalike_score, 4),
        "url_brand_in_path_flag": 1.0 if brand_in_path_count else 0.0,
        "generic_shortener_flag": 1.0 if shortener_count else 0.0,
    }
