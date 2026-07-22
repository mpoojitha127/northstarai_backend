"""
Centralized application configuration.

All environment-dependent values are read here, once, so the rest of the
codebase never touches os.environ directly. This keeps the application
provider-agnostic and allows seamless switching between local development,
production deployments, and future AI providers without code changes.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

    # ==========================================================
    # Application
    # ==========================================================
    APP_NAME: str = "NorthStar AI"
    ENVIRONMENT: str = "development"  # development | production | test

    API_V1_PREFIX: str = "/api/v1"

    FRONTEND_ORIGINS: str = (
        "http://localhost:5173,"
        "http://localhost:3000"
    )

    # ==========================================================
    # Database
    # ==========================================================
    DATABASE_URL: str = "sqlite:///./northstar.db"

    # ==========================================================
    # Authentication
    # ==========================================================
    JWT_SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION"
    JWT_ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # ==========================================================
    # AI Provider Configuration
    # ==========================================================

    # Supported:
    # - openrouter
    # - gemini
    #
    # Future:
    # - openai
    # - anthropic
    # - local models

    AI_PROVIDER: str = "openrouter"

    # ---------- Gemini ----------
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"

    # ---------- OpenRouter ----------
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "deepseek/deepseek-chat-v3.1"

    # ==========================================================
    # NorthStar AI Configuration
    # ==========================================================

    NORTHSTAR_ENABLED: bool = True

    # Minimum confidence before NorthStar raises a warning
    ALIGNMENT_THRESHOLD: float = 0.75

    # Maximum reasoning tokens reserved for reflection
    MAX_REFLECTION_TOKENS: int = 500

    # ==========================================================
    # Vector Memory
    # ==========================================================

    CHROMA_PERSIST_DIR: str = "./chroma_data"

    # ==========================================================
    # Helper Properties
    # ==========================================================

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.FRONTEND_ORIGINS.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    """
    Cached settings instance.

    Prevents reloading environment variables
    throughout the application.
    """
    return Settings()


settings = get_settings()