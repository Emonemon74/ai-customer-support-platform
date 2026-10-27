from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.ratelimit import RateLimiter
from app.core.settings import settings
from app.db.deps import get_db
from app.demo.service import DemoService
from app.schemas.auth import (
    DemoSessionResponse,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"],
)

_auth_rate_limit = RateLimiter("auth", per_minute=settings.RATE_LIMIT_AUTH_PER_MINUTE)
_demo_rate_limit = RateLimiter("demo", per_minute=settings.RATE_LIMIT_DEMO_PER_MINUTE)


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db),
    _: None = Depends(_auth_rate_limit),
):
    return TokenResponse(access_token=AuthService(db).register(request))


@router.post("/login", response_model=TokenResponse)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
    _: None = Depends(_auth_rate_limit),
):
    return TokenResponse(access_token=AuthService(db).login(request))


@router.post(
    "/demo",
    response_model=DemoSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def start_demo(
    db: Session = Depends(get_db),
    _: None = Depends(_demo_rate_limit),
):
    """Start a throw-away guest session pre-loaded with sample documents."""
    if not settings.DEMO_ENABLED:
        raise HTTPException(status_code=404, detail="Demo is not enabled")

    token, conversation_id = DemoService(db).create_session()
    return DemoSessionResponse(access_token=token, conversation_id=conversation_id)
