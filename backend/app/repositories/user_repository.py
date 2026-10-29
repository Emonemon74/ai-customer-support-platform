from datetime import datetime

from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_by_email(self, email: str) -> User | None:
        return (
            self.db.query(User)
            .filter(User.email == email)
            .first()
        )

    def create(
        self,
        full_name: str,
        email: str,
        hashed_password: str,
        is_demo: bool = False,
    ) -> User:

        user = User(
            full_name=full_name,
            email=email,
            hashed_password=hashed_password,
            is_demo=is_demo,
        )

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        return user

    def get_expired_demo_users(self, before: datetime, limit: int) -> list[User]:
        return (
            self.db.query(User)
            .filter(User.is_demo.is_(True), User.created_at < before)
            .order_by(User.created_at.asc())
            .limit(limit)
            .all()
        )

    def delete(self, user: User) -> None:
        self.db.delete(user)
        self.db.commit()
