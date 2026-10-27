from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.ratelimit import RateLimiter
from app.core.settings import settings
from app.db.deps import get_db
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.services.auth_service import AuthService

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"],
)

_auth_rate_limit = RateLimiter("auth", per_minute=settings.RATE_LIMIT_AUTH_PER_MINUTE)


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
