from app.services.feature_extraction import extract_features
from app.services.reputation_service import ReputationService


def test_verified_linkedin_sender_with_encoded_link_is_not_suspicious_for_encoding_only():
    payload = {
        "sender_email": "[local]@linkedin.com",
        "display_name": "LinkedIn",
        "subject": "Profile view",
        "body_text": "Someone viewed your profile.",
        "links": [
            {
                "href": "https://www.linkedin.com/comm/feed/update?trk=%7Bencoded%7D%252Ftracking%252Fvalue",
                "anchor_text": "View profile",
            }
        ],
        "domain": "linkedin.com",
        "html": None,
    }
    features = extract_features(payload)
    result = ReputationService().evaluate(payload, features)

    assert result["score"] == 0.0
    assert result["reasons"] == []


def test_unknown_encoded_link_still_gets_reputation_reason():
    payload = {
        "sender_email": "[local]@unknown.example",
        "display_name": "Unknown",
        "subject": "Profile view",
        "body_text": "Someone viewed your profile.",
        "links": [
            {
                "href": "https://unknown.example/track?x=%7Bencoded%7D%252Ftracking%252Fvalue%253D%2526",
                "anchor_text": "View profile",
            }
        ],
        "domain": "unknown.example",
        "html": None,
    }
    features = extract_features(payload)
    result = ReputationService().evaluate(payload, features)

    assert result["score"] > 0
    assert "URL contains heavy percent encoding" in result["reasons"]


def test_lookalike_and_brand_in_path_urls_increase_reputation():
    payload = {
        "sender_email": "[local]@login.microsoftonline.ccisystems.us",
        "display_name": "Microsoft",
        "subject": "Password expires soon",
        "body_text": "Open the secure page now.",
        "links": [
            {
                "href": "https://accounts-login.cz/google.com/reset",
                "anchor_text": "Google account",
            },
            {
                "href": "https://bit.ly/3xYzAbC",
                "anchor_text": "Reset password",
            },
        ],
        "domain": "login.microsoftonline.ccisystems.us",
        "html": None,
    }
    features = extract_features(payload)
    result = ReputationService().evaluate(payload, features)

    assert result["score"] >= 0.35
    assert "URL path contains a trusted brand domain while the real destination is unrelated" in result["reasons"]
    assert "URL uses a generic shortener that hides the final destination" in result["reasons"]
