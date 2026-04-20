from __future__ import annotations

from dataclasses import dataclass

from app.intelligence.verified_domains import VERIFIED_DOMAINS


@dataclass(frozen=True)
class Brand:
    name: str
    aliases: tuple[str, ...]
    domains: frozenset[str]


BRANDS: tuple[Brand, ...] = tuple(
    Brand(
        name=name,
        aliases=tuple(sorted({name.lower(), name.replace(" ", "").lower()})),
        domains=frozenset(domains),
    )
    for name, domains in VERIFIED_DOMAINS.items()
)


def brand_terms() -> set[str]:
    terms: set[str] = set()
    for brand in BRANDS:
        terms.add(brand.name.lower())
        terms.update(brand.aliases)
    return terms


def find_brand_mentions(text: str | None) -> list[Brand]:
    if not text:
        return []
    normalized = text.lower()
    matches: list[Brand] = []
    for brand in BRANDS:
        if brand.name.lower() in normalized or any(alias in normalized for alias in brand.aliases):
            matches.append(brand)
    return matches


def brand_for_verified_domain(domain: str | None) -> Brand | None:
    if not domain:
        return None
    normalized = domain.lower().strip(".")
    for brand in BRANDS:
        if normalized in brand.domains or any(normalized.endswith(f".{known}") for known in brand.domains):
            return brand
    return None
