from app.services.feature_extraction import extract_features


def test_feature_extraction_flags_mismatched_link_and_credentials():
    features = extract_features(
        {
            "sender_email": "[local]@paypa1-secure.example",
            "display_name": "PayPal Support",
            "subject": "Urgent: verify your account",
            "body_text": "Please verify your account immediately.",
            "links": [{"href": "https://paypa1-secure.example/login", "anchor_text": "paypal.com"}],
            "domain": "paypa1-secure.example",
            "html": "<form><input type='hidden' value='x'></form>",
        }
    )

    assert features["credential_phrase_count"] >= 1
    assert features["anchor_mismatch_flag"] == 1.0
    assert features["form_tag_presence"] == 1.0
    assert features["display_name_mismatch"] == 1.0


def test_feature_extraction_flags_random_sender_infrastructure():
    features = extract_features(
        {
            "sender_email": "[local]@yizpgeaj.fusionrift.uk.net",
            "display_name": "Unknown Sender",
            "subject": "Message",
            "body_text": "Please review this message.",
            "links": [],
            "domain": "yizpgeaj.fusionrift.uk.net",
            "html": None,
        }
    )

    assert features["random_subdomain_flag"] == 1.0
    assert features["suspicious_delegated_suffix_flag"] == 1.0
    assert features["domain_infrastructure_score"] >= 0.9


def test_feature_extraction_flags_prize_gambling_spam_language():
    features = extract_features(
        {
            "sender_email": "[local]@bluechip.io",
            "display_name": "Call Service Bluechip",
            "subject": "Lucky Coin",
            "body_text": (
                "Are you ready to flip your fate? Lucky Coin Challenge is here. "
                "Spin the magic coin for life-changing prizes, cash, free spins, "
                "and rewards. मुफ्त इनाम नकद किस्मत घुमाएं."
            ),
            "links": [],
            "domain": "bluechip.io",
            "html": None,
        }
    )

    assert features["spam_lure_keyword_count"] >= 4
    assert features["gambling_keyword_count"] >= 2
    assert features["hindi_spam_lure_count"] >= 4
    assert features["promotional_spam_score"] >= 0.45
    assert features["domain_infrastructure_score"] == 0.0


def test_feature_extraction_flags_homograph_and_brand_in_path_urls():
    features = extract_features(
        {
            "sender_email": "[local]@gοogle.com",
            "display_name": "Google",
            "subject": "Password expires soon",
            "body_text": "Your password expires in 15 minutes. Visit hxxps://accounts-login.cz/google[.]com now.",
            "links": [
                {
                    "href": "https://accounts-login.cz/google.com/reset",
                    "anchor_text": "google.com",
                }
            ],
            "domain": "gοogle.com",
            "html": None,
        }
    )

    assert features["homograph_flag"] == 1.0
    assert features["url_brand_in_path_flag"] == 1.0
    assert features["defanged_url_count"] >= 1
