from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "AI Customer Support Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    GROQ_API_KEY: str
    DATABASE_URL: str

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 3000000

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
