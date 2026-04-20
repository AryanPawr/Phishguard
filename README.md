# PhishGuard

PhishGuard is a full-stack phishing detection platform that combines a browser extension, FastAPI backend, structured machine learning pipeline, brand impersonation detection, local threat intelligence, and a JWT-protected analytics dashboard. It is designed as a cybersecurity portfolio project to demonstrate practical detection engineering across the browser, backend, and ML layers.

## Overview

PhishGuard detects suspicious email content across Gmail, Outlook Web, and generic web-rendered email pages. The extension extracts normalized message data, applies lightweight local heuristics, masks sensitive content, and sends a privacy-reduced payload to a backend API. The backend performs structured feature extraction, model inference, impersonation detection, and weighted score fusion before returning a risk assessment. Administrative telemetry is exposed through a dashboard and SIEM-friendly export format.

## Core Features

- Manifest V3 browser extension for Gmail, Outlook Web, and generic email-rendered pages
- Local client-side heuristics for urgency language, suspicious links, spoofing, and domain mismatch
- Privacy-first masking before backend submission
- FastAPI backend with request validation, scoring, persistence, and JWT-protected admin routes
- Structured phishing feature extraction pipeline
- TF-IDF + Logistic Regression baseline ML architecture with fallback inference
- Brand impersonation and lookalike-domain detection
- React + Tailwind analytics dashboard
- SIEM JSON export for downstream security workflows
- Threat intelligence registry and phishing rules
- Test coverage for backend, feature extraction, scoring, ML training, and extension manifest safety

## Architecture

```text
extension/      Browser extraction, local heuristics, masking, cache, UI banner
backend/        FastAPI API, feature extraction, ML inference, scoring, persistence
dashboard/      React + Tailwind admin interface
intelligence/   Brand registry, phishing rules, feed notes
shared/         JSON schemas for request/response/event contracts
infrastructure/ Docker Compose and nginx example config
tests/          API, ML, scoring, feature extraction, and extension tests
docs/           Architecture, security, ML pipeline, SIEM, deep-dive notes
````

## Detection Flow

1. A user opens an email in Gmail, Outlook Web, or another supported web-rendered email interface.
2. The extension extracts sender, display name, subject, body text, links, and context.
3. Local heuristics score obvious phishing signals and mask PII before transmission.
4. The backend validates the request and applies server-side masking again.
5. Structured features are extracted from text, links, domains, and available HTML.
6. The backend runs ML inference, impersonation detection, and reputation logic.
7. A weighted scoring engine produces a final classification and explanation.
8. The extension renders a real-time warning banner.
9. The backend stores anonymized telemetry for dashboard analytics and SIEM export.

## Technology Stack

### Extension

* Manifest V3
* JavaScript
* Content scripts
* Background service worker
* Custom banner UI

### Backend

* FastAPI
* Pydantic
* SQLAlchemy
* SQLite for local development
* JWT authentication
* In-process rate limiting

### Machine Learning

* scikit-learn
* TF-IDF vectorization
* Numeric structured features
* Logistic Regression
* joblib model artifact loading

### Dashboard

* React
* Vite
* Tailwind CSS

## Installation Guide

### Prerequisites

Install these before setup:

* Python 3.11+ or 3.12
* Node.js 18+ and npm
* Git
* A Chromium browser or Firefox

## Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

The backend runs on:

```text
http://localhost:8000
```

Health check:

```bash
curl http://localhost:8000/health
```

## Dashboard Setup

```bash
cd dashboard
npm install
cp .env.example .env
npm run dev
```

Open:

```text
http://localhost:5173
```

Default development credentials:

```text
username: admin
password: phishguard-admin
```

Change these in `backend/.env` before using the project outside local development.

## Extension Setup

### Chrome / Chromium

1. Open `chrome://extensions`
2. Enable Developer Mode
3. Click **Load unpacked**
4. Select the `extension/` folder

### Firefox

1. Open `about:debugging#/runtime/this-firefox`
2. Click **Load Temporary Add-on**
3. Select `extension/manifest.json`

The extension will call the local backend and display a risk banner when supported pages are opened.

## Production Integration

Current deployed endpoints:

- Backend URL: `https://phishguard-backend-anw5.onrender.com`
- Dashboard URL: `https://phishguard-dashboard.vercel.app`
- Dashboard env var: `VITE_API_BASE_URL=https://phishguard-backend-anw5.onrender.com/api`
- Backend CORS env var: `PHISHGUARD_CORS_ORIGINS=https://phishguard-dashboard.vercel.app`
- Extension default API URL: `https://phishguard-backend-anw5.onrender.com/api`

The backend reads CORS origins from `PHISHGUARD_CORS_ORIGINS`; keep localhost values only in local `.env` files when running the dashboard locally.

## Running the Test Suite

From the project root:

```bash
pytest
```

If you only want backend tests:

```bash
cd backend
source .venv/bin/activate
cd ..
pytest tests
```

## Model Training

The default model path is:

```text
backend/app/services/ml_engine/models/phishing_model.pkl
```

The checked-in model artifact can be treated as a placeholder or bootstrap artifact. If no valid trained model is available, the backend falls back to deterministic scoring behavior.

Train a baseline model from a CSV dataset:

```bash
cd backend
source .venv/bin/activate
python -m app.services.ml_engine.train --dataset ../data/phishing_training.csv
```

Expected dataset pattern:

* one text-like column such as `text`, `body`, `body_text`, `email`, `message`, `content`, or `url`
* one label-like column such as `phishing`, `malicious`, `spam`, `safe`, `legitimate`, `ham`, `1`, or `0`

## Scoring Strategy

The final score combines multiple independent signals:

```text
final_score =
0.30 * ml_probability +
0.25 * impersonation_score +
0.20 * heuristic_score +
0.15 * link_reputation +
0.10 * domain_registry_mismatch
```

This multi-signal design improves resilience and explainability by combining model output with deterministic security signals.

## Security Controls

* No raw email storage in persistent telemetry
* Sender, subject, and sample identifiers stored as hashes
* Client-side masking before backend submission
* Backend masking applied again server-side
* JWT-protected admin and SIEM routes
* Strict CORS configuration
* Input size limits and request validation
* Local rate limiting for API abuse resistance
* CSP controls in extension and nginx example configuration

## Phase 2: Model Training and Detection Maturity

Phase 1 establishes the platform and baseline detection pipeline. Phase 2 should focus on improving model quality, dataset realism, and evaluation rigor.

### Phase 2 Goals

* Replace placeholder or fallback behavior with a genuinely trained model
* Improve phishing and benign dataset quality
* Expand structured features for better generalization
* Benchmark multiple classifiers
* Measure precision, recall, F1, ROC-AUC, and false positive rate
* Add reproducible evaluation and model versioning
* Prepare the ML layer for transformer-based upgrades

### Recommended Phase 2 Work Plan

#### 1. Build a Better Training Dataset

Create a curated dataset from:

* phishing email datasets
* legitimate email and newsletter samples
* URL intelligence sources such as PhishTank or OpenPhish
* manually labeled examples for brand impersonation and lookalike domains

The target should include:

* phishing samples
* benign transactional emails
* benign security alerts
* newsletters and marketing emails
* brand impersonation examples
* deceptive anchor-text examples

#### 2. Normalize and Label Consistently

Standardize labels into:

* `1` for phishing or malicious
* `0` for benign or safe

Normalize:

* sender domain field
* body text formatting
* extracted links
* encoding artifacts
* duplicate records

#### 3. Expand Feature Engineering

Keep the existing pipeline and improve it with:

* better lookalike-domain similarity features
* public-suffix-aware domain parsing
* more robust anchor mismatch logic
* redirect-chain indicators
* language-specific phishing phrase sets
* improved suspicious TLD scoring
* optional HTML-derived form and hidden-element signals

#### 4. Benchmark Multiple Baselines

Compare at least:

* Logistic Regression
* Linear SVM
* Random Forest or Gradient Boosting on structured-only subsets

Retain the best model based on phishing recall and balanced false positive control.

#### 5. Add Proper Evaluation Output

Phase 2 should save:

* model version
* training date
* dataset source
* evaluation metrics
* confusion matrix
* feature importance or coefficient summaries where possible

Suggested artifact layout:

```text
backend/app/services/ml_engine/models/
backend/app/services/ml_engine/reports/
backend/app/services/ml_engine/experiments/
```

#### 6. Add Reproducible Experiment Scripts

Include scripts for:

* training
* evaluation
* model comparison
* exporting the best artifact

This will make the ML portion stronger for both GitHub and interviews.

#### 7. Prepare for Transformer Upgrade

Once the structured baseline is stable, Phase 2.5 or Phase 3 can explore:

* DistilBERT fine-tuning
* transformer embeddings combined with structured features
* ONNX runtime inference
* calibration between traditional and transformer outputs

The current architecture already supports this path because model inference is already treated as a replaceable backend component.

## Suggested Future Improvements

* PostgreSQL instead of SQLite for deployment
* Redis-backed distributed rate limiting
* RBAC and multi-user administration
* Feedback loop from dashboard into model improvement
* analyst review workflow for false positives and false negatives
* stronger Firefox messaging compatibility hardening
* optional threat feed ingestion jobs
* OCR or image-based phishing detection
* QR-code phishing detection
* cloud deployment and extension store packaging

## Project Status

Current state:

* end-to-end scaffold complete
* extension, backend, dashboard, tests, and docs included
* baseline ML pipeline included
* ready for dataset-driven Phase 2 training and evaluation

## Repository Topics

Recommended GitHub topics:

* cybersecurity
* phishing-detection
* browser-extension
* fastapi
* machine-learning
* threat-intelligence
* react
* detection-engineering

## License

MIT License.
