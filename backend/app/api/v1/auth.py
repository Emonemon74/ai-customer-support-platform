from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.ratelimit import RateLimiter
from app.core.settings import settings
from app.db.deps import get_db
from app.schemas.auth import AuthRequest, TokenResponse
from app.services.auth_service import AuthService

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"],
)

_auth_rate_limit = RateLimiter("auth", per_minute=settings.RATE_LIMIT_AUTH_PER_MINUTE)


@router.post("", response_model=TokenResponse)
def authenticate(
    request: AuthRequest,
    db: Session = Depends(get_db),
    _: None = Depends(_auth_rate_limit),
):
    token = AuthService(db).authenticate(request)

    return TokenResponse(
        access_token=token,
        token_type="bearer",
    )
