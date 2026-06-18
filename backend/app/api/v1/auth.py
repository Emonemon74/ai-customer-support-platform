from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.schemas.auth import AuthRequest, TokenResponse
from app.services.auth_service import AuthService

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"],
)


@router.post("", response_model=TokenResponse)
def authenticate(
    request: AuthRequest,
    db: Session = Depends(get_db),
):
    token = AuthService(db).authenticate(request)

    return TokenResponse(
        access_token=token,
        token_type="bearer",
    )