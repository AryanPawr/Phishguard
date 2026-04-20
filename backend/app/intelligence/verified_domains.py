from __future__ import annotations

from app.intelligence.domain_trust import TRUST_RECORDS, STRONG_SENDER_TYPES

VERIFIED_DOMAINS: dict[str, set[str]] = {
    "Apple": {"apple.com", "icloud.com"},
    "Amazon": {"amazon.com", "amazon.co.uk", "amazon.ca"},
    "Bank of America": {"bankofamerica.com", "bofa.com"},
    "Chase": {"chase.com", "jpmorgan.com"},
    "DHL": {"dhl.com"},
    "DocuSign": {"docusign.com", "docusign.net"},
    "Dropbox": {"dropbox.com"},
    "GitHub": {"github.com", "github.io"},
    "Google": {"google.com", "gmail.com", "accounts.google.com"},
    "LinkedIn": {"linkedin.com"},
    "Meta": {"facebook.com", "meta.com", "instagram.com"},
    "Microsoft": {"microsoft.com", "office.com", "outlook.com", "live.com"},
    "Netflix": {"netflix.com"},
    "PayPal": {"paypal.com", "paypalobjects.com"},
    "Slack": {"slack.com"},
    "Stripe": {"stripe.com"},
    "UPS": {"ups.com"},
    "Wells Fargo": {"wellsfargo.com"},
}

for record in TRUST_RECORDS:
    if record.trust_type in STRONG_SENDER_TYPES:
        VERIFIED_DOMAINS.setdefault(record.brand, set()).add(record.domain)


def all_verified_domains() -> set[str]:
    domains: set[str] = set()
    for values in VERIFIED_DOMAINS.values():
        domains.update(values)
    return domains
