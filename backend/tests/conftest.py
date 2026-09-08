"""Shared test fixtures.

Environment variables are set *before* any ``app`` import so that
``app.core.settings`` binds to a throwaway SQLite database and dummy secrets
instead of the real ``.env`` values.
"""

import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_ai_support.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("GROQ_API_KEY", "test-groq-key")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")

import pytest
from fastapi.testclient import TestClient

from app.db.base import Base
from app.db.deps import get_db
from app.db.session import SessionLocal, engine
from app.main import app

# Import every model so ``Base.metadata`` is complete before create_all.
from app.models import conversation, document, message, refresh_token, user  # noqa: F401


@pytest.fixture(autouse=True)
def _fresh_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def _stub_ai(monkeypatch):
    """Keep uploads away from pypdf / ChromaDB / Groq during tests."""

    class _StubVectorStore:
        def add_document(self, *args, **kwargs):
            return None

        def delete_document(self, *args, **kwargs):
            return None

    monkeypatch.setattr(
        "app.services.document_service.PDFParser.extract_pages",
        staticmethod(
            lambda file_path: [{"page_number": 1, "text": "stub document text " * 10}]
        ),
    )
    monkeypatch.setattr(
        "app.services.document_service.VectorStore", _StubVectorStore
    )
    monkeypatch.setattr(
        "app.services.conversation_service.generate_conversation_title",
        lambda question: "Refund policy questions",
    )


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    def _get_db_override():
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = _get_db_override
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _register(client: TestClient, email: str) -> str:
    response = client.post(
        "/api/v1/auth",
        json={"full_name": "Test User", "email": email, "password": "pw-12345"},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


@pytest.fixture
def user_a(client):
    token = _register(client, "user_a@example.com")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def user_b(client):
    token = _register(client, "user_b@example.com")
    return {"Authorization": f"Bearer {token}"}


PDF_BYTES = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n"


def make_conversation(client: TestClient, headers: dict) -> int:
    response = client.post(
        "/api/v1/conversations",
        json={"question": "How do refunds work?"},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]
