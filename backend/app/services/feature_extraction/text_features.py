from __future__ import annotations

from collections import Counter
import re

from app.intelligence.spoof_patterns import HIGH_RISK_PHRASES


URGENCY_KEYWORDS = {
    "act now",
    "asap",
    "deadline",
    "final notice",
    "immediately",
    "important",
    "limited time",
    "locked",
    "required",
    "suspended",
    "urgent",
    "within 24 hours",
}

CREDENTIAL_PHRASES = {
    "confirm your password",
    "login to continue",
    "password reset",
    "re-enter your password",
    "sign in to verify",
    "update credentials",
    "verify your account",
}

SPAM_LURE_PHRASES = {
    "cash",
    "claim",
    "free to play",
    "free spins",
    "jackpot",
    "life-changing prizes",
    "lottery",
    "lucky",
    "prize",
    "reward",
    "spin now",
    "winner",
}

GAMBLING_PHRASES = {
    "betting",
    "casino",
    "coin challenge",
    "free spins",
    "gamble",
    "jackpot",
    "slot",
    "spin",
    "wager",
}

HINDI_SPAM_LURE_PHRASES = {
    "इनाम",
    "किस्मत",
    "घुमाएं",
    "जीत",
    "नकद",
    "मुफ्त",
    "पुरस्कार",
}

TOKEN_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)
EMOJI_RE = re.compile(
    "["
    "\U0001f300-\U0001f5ff"
    "\U0001f600-\U0001f64f"
    "\U0001f680-\U0001f6ff"
    "\U0001f700-\U0001f77f"
    "\U0001f780-\U0001f7ff"
    "\U0001f800-\U0001f8ff"
    "\U0001f900-\U0001f9ff"
    "\U0001fa00-\U0001faff"
    "\u2600-\u26ff"
    "\u2700-\u27bf"
    "]",
    re.UNICODE,
)
DEFANGED_URL_RE = re.compile(r"\b(?:hxxps?|https?)://\S+|\b(?:[a-z0-9-]+\[\.\])+[a-z]{2,}\b", re.IGNORECASE)


def normalize_text(value: str | None) -> str:
    return " ".join((value or "").replace("\x00", " ").split())


def count_phrase_matches(text: str, phrases: set[str]) -> int:
    lowered = text.lower()
    return sum(1 for phrase in phrases if phrase in lowered)


def extract_text_features(subject: str | None, body_text: str | None) -> dict[str, float | str]:
    text = normalize_text(f"{subject or ''} {body_text or ''}")
    tokens = TOKEN_RE.findall(text.lower())
    counts = Counter(tokens)
    word_count = len(tokens)
    unique_ratio = len(counts) / word_count if word_count else 0.0
    uppercase_ratio = sum(1 for char in text if char.isupper()) / max(len(text), 1)
    exclamation_count = text.count("!")
    emoji_count = len(EMOJI_RE.findall(text))
    spam_lure_count = count_phrase_matches(text, SPAM_LURE_PHRASES)
    gambling_count = count_phrase_matches(text, GAMBLING_PHRASES)
    hindi_spam_lure_count = count_phrase_matches(text, HINDI_SPAM_LURE_PHRASES)
    promotional_spam_score = min(
        (spam_lure_count * 0.16)
        + (gambling_count * 0.18)
        + (hindi_spam_lure_count * 0.16)
        + min(emoji_count / 8, 1.0) * 0.18,
        1.0,
    )
    defanged_url_count = len(DEFANGED_URL_RE.findall(text))

    return {
        "body_text": text,
        "word_count": float(word_count),
        "unique_word_ratio": round(unique_ratio, 4),
        "uppercase_ratio": round(uppercase_ratio, 4),
        "exclamation_count": float(exclamation_count),
        "urgency_keyword_count": float(count_phrase_matches(text, URGENCY_KEYWORDS)),
        "credential_phrase_count": float(count_phrase_matches(text, CREDENTIAL_PHRASES)),
        "high_risk_phrase_count": float(count_phrase_matches(text, HIGH_RISK_PHRASES)),
        "spam_lure_keyword_count": float(spam_lure_count),
        "gambling_keyword_count": float(gambling_count),
        "hindi_spam_lure_count": float(hindi_spam_lure_count),
        "emoji_count": float(emoji_count),
        "defanged_url_count": float(defanged_url_count),
        "promotional_spam_score": round(promotional_spam_score, 4),
    }
