from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.security import create_access_token, require_admin, verify_admin_password
from app.database.repository import EventRepository
from app.database.session import get_db

router = APIRouter(prefix="/admin", tags=["admin"])


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=128)
    password: str = Field(..., min_length=1, max_length=256)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest) -> dict[str, str]:
    if not verify_admin_password(payload.username, payload.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid administrator credentials",
        )
    return {"access_token": create_access_token(payload.username), "token_type": "bearer"}


@router.get("/summary")
def summary(_: str = Depends(require_admin), db: Session = Depends(get_db)) -> dict[str, Any]:
    return EventRepository(db).summary()


@router.get("/recent")
def recent(
    limit: int = 25,
    _: str = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    return EventRepository(db).recent(limit)


@router.get("/trends")
def trends(
    days: int = 14,
    _: str = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    return EventRepository(db).recent_risk_events(days * 24)


@router.get("/brands")
def brands(
    limit: int = 10,
    _: str = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    return EventRepository(db).top_brands(limit)


@router.get("/feedback")
def feedback(
    limit: int = 50,
    _: str = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    return EventRepository(db).recent_feedback(limit)
