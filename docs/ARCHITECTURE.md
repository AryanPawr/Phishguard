# Architecture

PhishGuard uses a layered architecture:

1. Browser extension extracts message context from Gmail, Outlook Web, or generic email-rendered pages.
2. Extension heuristics perform local triage and mask PII.
3. FastAPI receives suspicious or cache-missed samples.
4. Server-side feature extraction creates structured text, link, domain, and HTML features.
5. The ML engine predicts phishing probability with the current baseline model or fallback scorer.
6. Brand impersonation and reputation checks add explainable risk signals.
7. The scoring engine returns a normalized assessment.
8. The database stores anonymized event metadata for analytics and SIEM export.

## Modularity

- `feature_extraction` can be reused by training and inference.
- `ml_engine` hides model loading behind `PhishingModel`.
- `impersonation_detector` and `reputation_service` are independent scoring providers.
- `shared/schemas` defines stable cross-component contracts.

## Scale Plan

- Replace SQLite with PostgreSQL.
- Move in-memory rate limiting to Redis.
- Send event writes to a queue when ingestion volume grows.
- Store threat intelligence in a managed table with source and expiry metadata.
- Add tenant-aware repositories and JWT claims.

