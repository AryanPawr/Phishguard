# Infrastructure

The local compose file runs the backend and Vite dashboard for portfolio demos.

Production hardening checklist:

- Replace SQLite with PostgreSQL.
- Move rate limiting to Redis or an API gateway.
- Use a long random `PHISHGUARD_JWT_SECRET`.
- Set `PHISHGUARD_CORS_ORIGINS=https://phishguard-dashboard.vercel.app`.
- Set `VITE_API_BASE_URL=https://phishguard-backend-anw5.onrender.com/api`.
- Confirm the extension default API URL is `https://phishguard-backend-anw5.onrender.com/api`.
- Terminate TLS before the backend.
- Ship `/api/siem/export` output to Splunk, Elastic, Sentinel, or Chronicle through a scheduled connector.

Current deployed endpoints:

- Backend URL: `https://phishguard-backend-anw5.onrender.com`
- Dashboard URL: `https://phishguard-dashboard.vercel.app`
