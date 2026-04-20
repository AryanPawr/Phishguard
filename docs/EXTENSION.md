# Extension

The extension is Manifest V3 and designed to work in Chromium and Firefox.

## Data Flow

1. Content scripts detect an email-like view.
2. Gmail, Outlook, or generic extractor returns a normalized payload.
3. Local heuristics score urgency, credential language, links, domain mismatch, and spoofing hints.
4. PII masking removes local-part email addresses, email addresses in text, phone-like values, and long tokens.
5. Suspicious samples are sent to `/api/analyze`.
6. Safe backend results are cached locally by a masked payload hash.
7. The risk banner renders the backend assessment.

## Privacy Guardrails

- The extension never stores raw email body text.
- Cache keys are SHA-256 hashes of masked payloads.
- Raw sender local-parts are replaced with `[local]`.
- Raw HTML is not sent by default.

## Permissions

The extension uses `storage` and host access for webmail and generic email-rendered websites. It does not request tab history, cookies, downloads, or clipboard access.

