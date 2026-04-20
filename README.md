# PhishGuard

PhishGuard is a hybrid AI-powered phishing detection platform built as a cybersecurity portfolio project. It combines a cross-browser webmail extension, FastAPI backend, structured ML pipeline, brand impersonation detection, local threat intelligence, analytics dashboard, and SIEM JSON export.

## Architecture

```text
extension/      Browser extraction, local heuristics, privacy masking, risk banner
backend/        FastAPI API, feature extraction, ML inference, scoring, JWT admin APIs
dashboard/      React + Tailwind admin console
intelligence/   Brand registry, phishing rules, feed notes
shared/         JSON schemas shared by client, backend, and SIEM workflows
infrastructure/ Docker Compose and nginx example config
tests/          Backend, ML, feature, spoofing, and extension manifest tests
docs/           Design notes and upgrade path
```

## Quick Start

### Backend

```bash
cd phishguard/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Health check:

```bash
curl http://localhost:8000/health
```

Analyze a sample:

```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "sender_email":"attacker@paypa1-secure.example",
    "display_name":"PayPal Support",
    "subject":"Urgent: verify your account",
    "body_text":"Sign in to verify your account immediately.",
    "links":[{"href":"https://paypa1-secure.example/login","anchor_text":"paypal.com"}],
    "domain":"paypa1-secure.example",
    "heuristic_score":0.8,
    "client_reasons":["Local heuristics flagged the message"],
    "source":"api"
  }'
```

### Dashboard

```bash
cd phishguard/dashboard
npm install
cp .env.example .env
npm run dev
```

Open `http://localhost:5173`. The default development credentials are `admin` and `phishguard-admin`. Change them in `backend/.env` before any shared demo.

### Extension

Chrome:

1. Open `chrome://extensions`.
2. Enable Developer mode.
3. Load unpacked extension from `phishguard/extension`.

Firefox:

1. Open `about:debugging#/runtime/this-firefox`.
2. Load temporary add-on.
3. Select `phishguard/extension/manifest.json`.

The extension sends only masked content and URL metadata to the backend. Safe backend results are cached locally for a short TTL.

## ML Training

The default model path is:

```text
backend/app/services/ml_engine/models/phishing_model.pkl
```

The checked-in file is a placeholder. The backend falls back to deterministic scoring until a real joblib artifact is trained.

Train with a CSV containing a text-like column and a label-like column:

```bash
cd phishguard/backend
python -m app.services.ml_engine.train --dataset ../data/phishing_training.csv
```

Accepted text columns include `text`, `body`, `body_text`, `email`, `message`, `content`, and `url`. Accepted labels include `phishing`, `malicious`, `spam`, `safe`, `legitimate`, `ham`, `1`, and `0`.

## Scoring

The backend combines:

```text
final_score =
0.30 * ml_probability +
0.25 * impersonation_score +
0.20 * heuristic_score +
0.15 * link_reputation +
0.10 * domain_registry_mismatch
```

Responses follow:

```json
{
  "risk_score": 0.81,
  "classification": "phishing",
  "confidence": "high",
  "reasons": ["Sender identity references a brand from an unverified domain"]
}
```

## Security Controls

- No raw email storage.
- Sender, subject, and sample identifiers are stored as hashes.
- Extension masks PII before API submission.
- Backend masks PII again before feature extraction.
- JWT-protected admin and SIEM APIs.
- Strict CORS configuration.
- In-process rate limiting for local demo use.
- CSP in the extension and nginx example.
- Input size limits and Pydantic validation.

## Tests

```bash
cd phishguard
pytest
```

## Upgrade Path

The system is ready for:

- DistilBERT or transformer feature service.
- ONNX model serving.
- PostgreSQL and Redis-backed rate limiting.
- Multi-tenant organization IDs and RBAC.
- Threat-sharing feed export with privacy-preserving indicators.

