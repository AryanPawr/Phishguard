# SIEM Export

The SIEM endpoint returns normalized JSON:

```http
GET /api/siem/export?limit=100
Authorization: Bearer <admin-jwt>
```

Example event fields:

```json
{
  "event.kind": "alert",
  "event.category": ["email", "threat"],
  "event.type": ["indicator"],
  "event.module": "phishguard",
  "threat.indicator.type": "email",
  "phishguard.sample_hash": "abc123",
  "phishguard.risk_score": 0.82,
  "phishguard.classification": "phishing"
}
```

This shape maps cleanly into Elastic Common Schema style fields while preserving PhishGuard-specific fields.

