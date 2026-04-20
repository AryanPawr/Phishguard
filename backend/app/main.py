from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import admin, analyze, feedback, siem
from app.core.config import get_settings
from app.core.security import RateLimitMiddleware
from app.database.session import init_db


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Hybrid AI-powered phishing detection API.",
)

app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "phishguard-backend"}


app.include_router(analyze.router, prefix=settings.api_prefix)
app.include_router(feedback.router, prefix=settings.api_prefix)
app.include_router(admin.router, prefix=settings.api_prefix)
app.include_router(siem.router, prefix=settings.api_prefix)
