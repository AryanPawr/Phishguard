from app.services.scoring_engine import ScoringEngine


def test_weighted_scoring_classifies_phishing():
    result = ScoringEngine().score(
        ml_probability=0.94,
        impersonation_score=0.9,
        heuristic_score=0.85,
        link_reputation=0.8,
        domain_registry_mismatch=1.0,
        reasons=["test"],
    )

    assert result["classification"] == "phishing"
    assert result["risk_score"] >= 0.72
    assert result["confidence"] == "high"


def test_high_reputation_risk_cannot_be_classified_safe():
    result = ScoringEngine().score(
        ml_probability=0.05,
        impersonation_score=0.0,
        heuristic_score=0.0,
        link_reputation=0.95,
        domain_registry_mismatch=0.0,
        reasons=["random sender infrastructure"],
    )

    assert result["classification"] == "suspicious"
    assert result["risk_score"] >= 0.32


def test_prize_lure_reason_cannot_be_classified_safe():
    result = ScoringEngine().score(
        ml_probability=0.08,
        impersonation_score=0.0,
        heuristic_score=0.0,
        link_reputation=0.0,
        domain_registry_mismatch=0.0,
        reasons=["Message contains gambling or prize-lure spam language"],
    )

    assert result["classification"] == "suspicious"


def test_lookalike_reason_cannot_be_classified_safe():
    result = ScoringEngine().score(
        ml_probability=0.08,
        impersonation_score=0.0,
        heuristic_score=0.0,
        link_reputation=0.0,
        domain_registry_mismatch=0.0,
        reasons=["URL contains lookalike brand or homograph indicators"],
    )

    assert result["classification"] == "suspicious"


def test_trusted_noreply_sender_receives_small_risk_reduction():
    result = ScoringEngine().score(
        ml_probability=0.2,
        impersonation_score=0.0,
        heuristic_score=0.1,
        link_reputation=0.0,
        domain_registry_mismatch=0.0,
        trusted_sender=True,
        sender_local_category="noreply",
        reasons=[],
    )

    assert result["risk_score"] == 0.04
