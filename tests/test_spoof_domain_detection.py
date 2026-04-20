from app.services.feature_extraction.domain_features import extract_domain_features, levenshtein
from app.services.impersonation_detector import ImpersonationDetector


def test_levenshtein_detects_close_brand_lookalike():
    assert levenshtein("paypa1", "paypal") == 1


def test_impersonation_detector_scores_brand_mismatch():
    payload = {
        "sender_email": "[local]@paypa1-secure.example",
        "display_name": "PayPal Support",
        "subject": "Verify your account",
        "body_text": "",
        "domain": "paypa1-secure.example",
    }
    features = extract_domain_features(
        payload["domain"],
        payload["sender_email"],
        payload["display_name"],
        payload["subject"],
    )
    result = ImpersonationDetector().evaluate(payload, features)

    assert result["score"] > 0.3
    assert result["brand"] == "PayPal"


def test_verified_brand_domain_is_not_counted_as_impersonation():
    payload = {
        "sender_email": "[local]@linkedin.com",
        "display_name": "LinkedIn",
        "subject": "New profile view",
        "body_text": "",
        "domain": "linkedin.com",
    }
    features = extract_domain_features(
        payload["domain"],
        payload["sender_email"],
        payload["display_name"],
        payload["subject"],
    )
    result = ImpersonationDetector().evaluate(payload, features)

    assert result["score"] == 0.0
    assert result["brand"] is None


def test_random_infrastructure_domain_does_not_get_fake_brand_attribution():
    payload = {
        "sender_email": "[local]@yizpgeaj.fusionrift.uk.net",
        "display_name": "Unknown Sender",
        "subject": "Message",
        "body_text": "Win an iPhone today",
        "domain": "yizpgeaj.fusionrift.uk.net",
    }
    features = extract_domain_features(
        payload["domain"],
        payload["sender_email"],
        payload["display_name"],
        payload["subject"],
    )
    result = ImpersonationDetector().evaluate(payload, features)

    assert result["brand"] is None
