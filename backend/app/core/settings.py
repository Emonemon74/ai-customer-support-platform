from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "AI Customer Support Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    GROQ_API_KEY: str
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    DATABASE_URL: str

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day; override via env

    # --- Retrieval ---------------------------------------------------------
    # "vector"  -> dense only (original behaviour, kept for the eval baseline)
    # "hybrid"  -> dense + BM25 fused
    # "rerank"  -> hybrid candidates re-scored by a cross-encoder (default)
    RETRIEVAL_MODE: str = "rerank"
    RETRIEVAL_DENSE_K: int = 20
    RETRIEVAL_BM25_K: int = 20
    RETRIEVAL_RRF_K: int = 60
    RETRIEVAL_TOP_N: int = 5
    RERANKER_MODEL: str = "ms-marco-MiniLM-L-12-v2"
    # Minimum reranker score for a chunk to be treated as relevant context.
    # Below this the answer path is given empty context and must abstain.
    RETRIEVAL_MIN_SCORE: float = 0.15

    # --- Async document ingestion ---------------------------------------
    # When DOCUMENT_QUEUE_ASYNC is false the upload endpoint processes the
    # document inline (used by tests, CI and simple local runs). In the
    # Docker stack it is true and an RQ worker drains the queue.
    REDIS_URL: str = "redis://localhost:6379/0"
    DOCUMENT_QUEUE_ASYNC: bool = False
    DOCUMENT_QUEUE_NAME: str = "documents"
    DOCUMENT_MAX_RETRIES: int = 3

    # --- Rate limiting ---------------------------------------------------
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_AUTH_PER_MINUTE: int = 10
    RATE_LIMIT_CHAT_PER_MINUTE: int = 30

    BACKEND_CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"
    BACKEND_CORS_ORIGIN_REGEX: str = ""

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.BACKEND_CORS_ORIGINS.split(",")
            if origin.strip()
        ]

    @property
    def cors_origin_regex(self) -> str | None:
        return self.BACKEND_CORS_ORIGIN_REGEX.strip() or None

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        extra="ignore"
    )


settings = Settings()
