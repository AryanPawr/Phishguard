# Threat Intelligence Feeds

PhishGuard is wired for local threat intelligence first and can later ingest external feeds into the same registry shape.

Supported training and enrichment sources:

- Kaggle phishing email and URL datasets
- Enron spam and ham email corpus
- PhishTank URL feed
- OpenPhish feed

Recommended ingestion flow:

1. Normalize feed records into `url`, `domain`, `brand`, `first_seen`, `source`, and `confidence`.
2. Store raw external feed data outside the application database.
3. Import only indicators, hashes, and metadata into PhishGuard.
4. Expire indicators by source-specific TTL.
5. Keep customer email text out of threat-sharing exports.

