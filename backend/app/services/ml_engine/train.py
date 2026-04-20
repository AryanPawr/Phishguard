from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from app.core.config import get_settings
from app.services.feature_extraction import extract_features
from app.services.ml_engine.inference import MODEL_VERSION, NUMERIC_FEATURE_COLUMNS

URL_RE = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)


def normalize_label(value: Any) -> int:
    text = str(value).strip().lower()
    if text in {"1", "true", "phish", "phishing", "malicious", "spam"}:
        return 1
    if text in {"0", "false", "safe", "legitimate", "ham", "benign"}:
        return 0
    raise ValueError(f"Unsupported label value: {value!r}")


def detect_columns(frame: pd.DataFrame) -> tuple[str, str]:
    text_candidates = ["text", "body", "body_text", "email", "message", "content", "url"]
    label_candidates = ["label", "target", "class", "is_phishing", "phishing"]
    text_column = next((column for column in text_candidates if column in frame.columns), None)
    label_column = next((column for column in label_candidates if column in frame.columns), None)
    if not text_column or not label_column:
        raise ValueError(
            "Dataset must contain a text column "
            f"({', '.join(text_candidates)}) and label column ({', '.join(label_candidates)})."
        )
    return text_column, label_column


def links_from_text(text: str) -> list[dict[str, str]]:
    return [{"href": match.group(0), "anchor_text": match.group(0)} for match in URL_RE.finditer(text)]


def build_training_frame(dataset_path: Path) -> pd.DataFrame:
    raw = pd.read_csv(dataset_path)
    text_column, label_column = detect_columns(raw)
    rows: list[dict[str, Any]] = []
    for _, source_row in raw.iterrows():
        text = str(source_row.get(text_column, ""))
        payload = {
            "sender_email": str(source_row.get("sender_email", "")),
            "display_name": str(source_row.get("display_name", "")),
            "subject": str(source_row.get("subject", "")),
            "body_text": text,
            "links": links_from_text(text),
            "domain": str(source_row.get("domain", "")),
            "html": str(source_row.get("html", "")),
        }
        features = extract_features(payload)
        rows.append(
            {
                "label": normalize_label(source_row[label_column]),
                "body_text": features.get("body_text", text),
                **{column: float(features.get(column, 0) or 0) for column in NUMERIC_FEATURE_COLUMNS},
            }
        )
    return pd.DataFrame(rows)


def train_model(dataset_path: Path, output_path: Path | None = None) -> dict[str, Any]:
    settings = get_settings()
    output_path = output_path or settings.model_path
    frame = build_training_frame(dataset_path)
    class_counts = frame["label"].value_counts()
    test_size = 0.25 if len(frame) >= 8 else 0.5
    can_stratify = frame["label"].nunique() > 1 and class_counts.min() >= 2
    x_train, x_test, y_train, y_test = train_test_split(
        frame.drop(columns=["label"]),
        frame["label"],
        test_size=test_size,
        random_state=42,
        stratify=frame["label"] if can_stratify else None,
    )

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "tfidf",
                TfidfVectorizer(max_features=8000, ngram_range=(1, 2), min_df=1),
                "body_text",
            ),
            ("numeric", StandardScaler(with_mean=False), NUMERIC_FEATURE_COLUMNS),
        ],
        sparse_threshold=0.3,
    )

    pipeline = Pipeline(
        steps=[
            ("features", preprocessor),
            (
                "classifier",
                LogisticRegression(
                    max_iter=1000,
                    class_weight="balanced",
                    solver="liblinear",
                ),
            ),
        ]
    )
    pipeline.fit(x_train, y_train)
    probabilities = pipeline.predict_proba(x_test)[:, 1]
    predictions = pipeline.predict(x_test)
    metrics = {
        "classification_report": classification_report(y_test, predictions, output_dict=True),
        "roc_auc": float(roc_auc_score(y_test, probabilities)) if y_test.nunique() > 1 else None,
        "rows": int(len(frame)),
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "pipeline": pipeline,
            "version": MODEL_VERSION,
            "numeric_columns": NUMERIC_FEATURE_COLUMNS,
            "metrics": metrics,
        },
        output_path,
    )
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the PhishGuard structured baseline model.")
    parser.add_argument("--dataset", required=True, type=Path, help="CSV dataset with text and label columns")
    parser.add_argument("--output", type=Path, default=None, help="Output joblib path")
    args = parser.parse_args()
    metrics = train_model(args.dataset, args.output)
    print(metrics)


if __name__ == "__main__":
    main()
