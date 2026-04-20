# Security

PhishGuard is intentionally privacy-preserving.

## Data Handling

- Raw email content is not persisted.
- Sender and subject values are HMAC-hashed for analytics.
- Message samples are SHA-256 hashed.
- Client and server both mask PII.
- SIEM export contains indicators, classifications, and reasons, not raw content.

## API Security

- JWT admin authentication protects analytics and SIEM routes.
- CORS is configured by explicit origins.
- Request size is constrained through Pydantic field limits.
- Rate limiting is included for local demos.

## Production Hardening

- Rotate `PHISHGUARD_JWT_SECRET`.
- Use managed secrets.
- Add TLS.
- Add audit logs for admin access.
- Add Redis-backed rate limiting.
- Add organization-scoped JWT claims before multi-tenant use.

