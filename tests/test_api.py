from fastapi.testclient import TestClient

from app.main import app
from app.database.session import init_db


init_db()
client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_analyze_endpoint_returns_structured_assessment():
    response = client.post(
        "/api/analyze",
        json={
            "sender_email": "attacker@paypa1-secure.example",
            "display_name": "PayPal Support",
            "subject": "Urgent: verify your account",
            "body_text": "Sign in to verify your account immediately.",
            "links": [{"href": "https://paypa1-secure.example/login", "anchor_text": "paypal.com"}],
            "domain": "paypa1-secure.example",
            "heuristic_score": 0.8,
            "client_reasons": ["Local heuristics flagged the message"],
            "source": "generic",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["classification"] in {"suspicious", "phishing"}
    assert 0 <= body["risk_score"] <= 1
    assert body["sample_hash"]


def test_feedback_endpoint_records_pending_review_feedback():
    response = client.post(
        "/api/feedback",
        json={
            "sample_hash": "a" * 64,
            "domain": "linkedin.com",
            "source": "gmail",
            "current_risk_score": 0.34,
            "current_classification": "suspicious",
            "user_feedback": "mark_not_risky",
            "reasons": ["URL contains heavy percent encoding"],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "received"
    assert body["review_status"] == "pending"


def test_admin_feedback_queue_requires_jwt_and_returns_feedback():
    unauthorized = client.get("/api/admin/feedback")
    assert unauthorized.status_code in {401, 403}

    token_response = client.post(
        "/api/admin/login",
        json={"username": "admin", "password": "phishguard-admin"},
    )
    assert token_response.status_code == 200
    token = token_response.json()["access_token"]

    response = client.get("/api/admin/feedback", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)
