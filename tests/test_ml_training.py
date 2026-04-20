import pandas as pd

from app.services.ml_engine.train import train_model


def test_training_pipeline_writes_model(tmp_path):
    dataset = tmp_path / "training.csv"
    model = tmp_path / "phishing_model.pkl"
    pd.DataFrame(
        [
            {"text": "verify your account password now http://paypa1.example/login", "label": "phishing"},
            {"text": "urgent payment failed sign in http://billing-alert.example", "label": "phishing"},
            {"text": "confirm your identity immediately http://secure-login.example", "label": "phishing"},
            {"text": "team lunch moved to Thursday", "label": "safe"},
            {"text": "project notes attached for review", "label": "safe"},
            {"text": "weekly report is ready", "label": "safe"},
        ]
    ).to_csv(dataset, index=False)

    metrics = train_model(dataset, model)

    assert model.exists()
    assert metrics["rows"] == 6

