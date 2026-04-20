# Infrastructure

The local compose file runs the backend and Vite dashboard for portfolio demos.

Production hardening checklist:

- Replace SQLite with PostgreSQL.
- Move rate limiting to Redis or an API gateway.
- Use a long random `PHISHGUARD_JWT_SECRET`.
- Set one exact dashboard origin in `PHISHGUARD_CORS_ORIGINS`.
- Terminate TLS before the backend.
- Ship `/api/siem/export` output to Splunk, Elastic, Sentinel, or Chronicle through a scheduled connector.

