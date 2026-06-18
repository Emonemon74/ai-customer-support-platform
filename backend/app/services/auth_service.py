from sqlalchemy.orm import Session

from app.core.exceptions.auth import AuthenticationError
from app.core.security.jwt import create_access_token
from app.core.security.password import hash_password, verify_password
from app.repositories.user_repository import UserRepository
from app.schemas.auth import AuthRequest


class AuthService:

    def __init__(self, db: Session):
        self.user_repository = UserRepository(db)

    def authenticate(self, request: AuthRequest) -> str:
        user = self.user_repository.get_by_email(request.email)

        if user:
            if not verify_password(request.password, user.hashed_password):
                raise AuthenticationError("Invalid email or password")

            return create_access_token({"sub": user.email})

        if not request.full_name:
            raise AuthenticationError("Full name is required for signup")

        hashed_password = hash_password(request.password)

        new_user = self.user_repository.create(
            full_name=request.full_name,
            email=request.email,
            hashed_password=hashed_password,
        )

        return create_access_token({"sub": new_user.email})