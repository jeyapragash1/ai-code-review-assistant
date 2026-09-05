from functools import lru_cache
from typing import Annotated

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: Annotated[
        str,
        Field(
            validation_alias="APP_NAME",
            default="AI-Powered GitHub Code Review Assistant API",
        ),
    ]
    app_version: Annotated[str, Field(validation_alias="APP_VERSION", default="0.1.0")]
    app_env: Annotated[str, Field(validation_alias="APP_ENV", default="development")]
    debug: Annotated[bool, Field(validation_alias="DEBUG", default=False)]
    api_v1_prefix: Annotated[
        str,
        Field(validation_alias="API_V1_PREFIX", default="/api/v1"),
    ]
    frontend_url: Annotated[
        str,
        Field(validation_alias="FRONTEND_URL", default="http://localhost:3000"),
    ]
    database_url: Annotated[
        str,
        Field(
            validation_alias="DATABASE_URL",
            default="postgresql+psycopg://localhost:5432/ai_code_review_db",
        ),
    ]
    github_token: Annotated[str, Field(validation_alias="GITHUB_TOKEN", default="")]
    github_webhook_secret: Annotated[
        str,
        Field(validation_alias="GITHUB_WEBHOOK_SECRET", default=""),
    ]
    github_webhook_max_body_bytes: Annotated[
        int,
        Field(validation_alias="GITHUB_WEBHOOK_MAX_BODY_BYTES", default=2 * 1024 * 1024),
    ]
    gemini_api_key: Annotated[str, Field(validation_alias="GEMINI_API_KEY", default="")]

    @property
    def cors_origins(self) -> list[str]:
        return [self.frontend_url]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
