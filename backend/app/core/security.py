from __future__ import annotations

import hashlib
import hmac
import json
import re
import time
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import Settings, get_settings


EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE_RE = re.compile(r"(?<!\d)(?:\+?\d[\d\s().-]{7,}\d)(?!\d)")
CREDIT_CARD_LIKE_RE = re.compile(r"\b(?:\d[ -]*?){13,19}\b")
TOKEN_RE = re.compile(r"\b[A-Za-z0-9_-]{32,}\b")
NOREPLY_RE = re.compile(r"^(?:no-?reply|do-?not-?reply|donotreply)$", re.IGNORECASE)
NOTIFICATION_RE = re.compile(r"^(?:notification|notifications|alert|alerts|updates?)$", re.IGNORECASE)
SUPPORT_RE = re.compile(r"^(?:support|help|service|customer-service|callsupport)$", re.IGNORECASE)

bearer_scheme = HTTPBearer(auto_error=False)
_RATE_BUCKETS: dict[tuple[str, int], int] = {}


def mask_pii_text(value: str | None) -> str:
    if not value:
        return ""
    masked = EMAIL_RE.sub("[email]", value)
    masked = PHONE_RE.sub("[phone]", masked)
    masked = CREDIT_CARD_LIKE_RE.sub("[number]", masked)
    return TOKEN_RE.sub("[token]", masked)


def mask_email_address(value: str | None) -> str:
    if not value or "@" not in value:
        return mask_pii_text(value)
    _, domain = value.rsplit("@", 1)
    return f"[local]@{domain.lower()}"


def sender_local_category(value: str | None) -> str:
    if not value or "@" not in value:
        return "unknown"
    local_part = value.rsplit("@", 1)[0].strip().lower()
    if NOREPLY_RE.match(local_part):
        return "noreply"
    if NOTIFICATION_RE.match(local_part):
        return "notification"
    if SUPPORT_RE.match(local_part):
        return "support"
    return "unknown"


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def hmac_hash(value: str | None, settings: Settings | None = None) -> str:
    settings = settings or get_settings()
    digest = hmac.new(
        settings.jwt_secret.encode("utf-8"),
        (value or "").encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return digest


def mask_payload(payload: dict[str, Any]) -> dict[str, Any]:
    masked = dict(payload)
    masked["sender_local_category"] = masked.get("sender_local_category") or sender_local_category(
        masked.get("sender_email")
    )
    masked["sender_email"] = mask_email_address(masked.get("sender_email"))
    masked["display_name"] = mask_pii_text(masked.get("display_name"))
    masked["subject"] = mask_pii_text(masked.get("subject"))
    masked["body_text"] = mask_pii_text(masked.get("body_text"))
    masked["links"] = [
        {
            "href": str(link.get("href", ""))[:2048],
            "anchor_text": mask_pii_text(link.get("anchor_text", ""))[:512],
        }
        for link in masked.get("links", [])
        if isinstance(link, dict)
    ]
    return masked


def create_access_token(subject: str, settings: Settings | None = None) -> str:
    settings = settings or get_settings()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expiration_minutes)
    payload = {"sub": subject, "exp": expires_at, "scope": "admin"}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def verify_admin_password(username: str, password: str, settings: Settings | None = None) -> bool:
    settings = settings or get_settings()
    return hmac.compare_digest(username, settings.admin_username) and hmac.compare_digest(
        password,
        settings.admin_password,
    )


def require_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    settings: Settings = Depends(get_settings),
) -> str:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    if payload.get("scope") != "admin" or not payload.get("sub"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin scope required")
    return str(payload["sub"])


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        settings = get_settings()
        if request.url.path.endswith("/health"):
            return await call_next(request)

        client = request.headers.get("x-forwarded-for", request.client.host if request.client else "local")
        minute_window = int(time.time() // 60)
        key = (client.split(",")[0].strip(), minute_window)
        _RATE_BUCKETS[key] = _RATE_BUCKETS.get(key, 0) + 1

        stale_window = minute_window - 2
        for bucket_key in list(_RATE_BUCKETS):
            if bucket_key[1] < stale_window:
                _RATE_BUCKETS.pop(bucket_key, None)

        if _RATE_BUCKETS[key] > settings.rate_limit_per_minute:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded", "retry_after_seconds": 60},
                headers={"Retry-After": "60"},
            )
        return await call_next(request)
