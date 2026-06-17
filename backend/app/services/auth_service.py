from sqlalchemy.orm import Session

from app.core.exceptions.auth import AuthenticationError, EmailAlreadyExistsError
from app.core.security.jwt import create_access_token
from app.core.security.password import hash_password, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest


class AuthService:

    def __init__(self, db: Session):
        self.user_repository = UserRepository(db)

    def register(self, request: RegisterRequest) -> User:
        existing_user = self.user_repository.get_by_email(request.email)

        if existing_user:
            raise EmailAlreadyExistsError()

        hashed_password = hash_password(request.password)

        return self.user_repository.create(
            full_name=request.full_name,
            email=request.email,
            hashed_password=hashed_password,
        )

    def login(self, request: LoginRequest) -> str:
        user = self.user_repository.get_by_email(request.email)

        if not user:
            raise AuthenticationError("Invalid email or password")

        if not verify_password(request.password, user.hashed_password):
            raise AuthenticationError("Invalid email or password")

        return create_access_token(
            {
                "sub": user.email
            }
        )