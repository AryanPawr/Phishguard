# ML Pipeline

The baseline model combines TF-IDF text vectors with structured numeric features and Logistic Regression.

## Feature Groups

Text:

- TF-IDF vectors
- Urgency keyword count
- Credential harvesting phrase count
- High-risk phrase count
- Uppercase and punctuation signals

Links:

- URL count
- Anchor mismatch flag
- URL entropy
- IP-based URL flag
- Suspicious TLD score
- Encoded character count

Domain:

- Levenshtein distance to known brands
- Subdomain depth
- Punycode detection
- Display name mismatch
- Registry mismatch

Structure:

- HTML to text ratio
- Form tag presence
- Hidden element count

## Datasets

The training script accepts normalized CSV exports from:

- Kaggle phishing datasets
- Enron spam dataset
- PhishTank URL feed
- OpenPhish feed

## Transformer Upgrade

To add DistilBERT later, keep the structured features and replace the TF-IDF branch with an embedding provider. For production deployment, export the transformer to ONNX and add a model-serving adapter behind `PhishingModel`.

