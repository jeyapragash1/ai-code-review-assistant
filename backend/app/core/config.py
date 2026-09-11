from functools import lru_cache
from typing import Annotated, Literal

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        hide_input_in_errors=True,
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
    github_app_client_id: Annotated[str, Field(validation_alias="GITHUB_APP_CLIENT_ID", default="")]
    github_app_client_secret: Annotated[SecretStr, Field(validation_alias="GITHUB_APP_CLIENT_SECRET", default=SecretStr(""))]
    github_oauth_callback_url: str = Field(default="http://localhost:8000/api/v1/auth/github/callback")
    auth_allowed_github_logins: str = Field(default="jeyapragash1")
    auth_session_cookie_name: str = Field(default="codereview_session", pattern=r"^[A-Za-z0-9_-]{1,128}$")
    auth_session_ttl_seconds: int = Field(default=604800, ge=300, le=2_592_000)
    auth_oauth_state_ttl_seconds: int = Field(default=600, ge=60, le=3600)
    auth_cookie_secure: bool = Field(default=False)
    auth_cookie_samesite: Literal["lax", "strict"] = Field(default="lax")
    github_api_base_url: Literal["https://api.github.com"] = "https://api.github.com"
    github_api_version: Literal["2026-03-10"] = "2026-03-10"
    github_repository_owner: str = Field(default="Jeyapragash1", pattern=r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$")
    github_repository_name: str = Field(default="ai-code-review-assistant", pattern=r"^[A-Za-z0-9_-][A-Za-z0-9_.-]{0,99}$")
    github_request_timeout_seconds: float = Field(default=15, gt=0, le=60)
    github_max_retries: int = Field(default=3, ge=0, le=5)
    github_webhook_secret: Annotated[
        str,
        Field(validation_alias="GITHUB_WEBHOOK_SECRET", default=""),
    ]
    github_webhook_max_body_bytes: Annotated[
        int,
        Field(validation_alias="GITHUB_WEBHOOK_MAX_BODY_BYTES", default=2 * 1024 * 1024),
    ]
    static_review_max_changed_files: Annotated[
        int,
        Field(validation_alias="STATIC_REVIEW_MAX_CHANGED_FILES", default=50, ge=1, le=500),
    ]
    static_review_max_file_bytes: Annotated[
        int,
        Field(validation_alias="STATIC_REVIEW_MAX_FILE_BYTES", default=262_144, ge=1_024, le=2 * 1024 * 1024),
    ]
    static_review_max_total_bytes: Annotated[
        int,
        Field(validation_alias="STATIC_REVIEW_MAX_TOTAL_BYTES", default=1_048_576, ge=1_024, le=10 * 1024 * 1024),
    ]
    static_review_analyzer_timeout_seconds: Annotated[
        float,
        Field(validation_alias="STATIC_REVIEW_ANALYZER_TIMEOUT_SECONDS", default=10, gt=0, le=60),
    ]
    static_review_max_findings: Annotated[
        int,
        Field(validation_alias="STATIC_REVIEW_MAX_FINDINGS", default=100, ge=1, le=1_000),
    ]
    static_review_max_patch_bytes: Annotated[
        int,
        Field(validation_alias="STATIC_REVIEW_MAX_PATCH_BYTES", default=131_072, ge=1_024, le=2 * 1024 * 1024),
    ]
    static_review_max_title_length: Annotated[
        int,
        Field(validation_alias="STATIC_REVIEW_MAX_TITLE_LENGTH", default=255, ge=40, le=255),
    ]
    static_review_max_problem_length: Annotated[
        int,
        Field(validation_alias="STATIC_REVIEW_MAX_PROBLEM_LENGTH", default=2_000, ge=100, le=10_000),
    ]
    static_review_max_explanation_length: Annotated[
        int,
        Field(validation_alias="STATIC_REVIEW_MAX_EXPLANATION_LENGTH", default=2_000, ge=100, le=10_000),
    ]
    static_review_max_suggestion_length: Annotated[
        int,
        Field(validation_alias="STATIC_REVIEW_MAX_SUGGESTION_LENGTH", default=2_000, ge=100, le=10_000),
    ]
    static_review_validation_confidence_threshold: Annotated[
        float,
        Field(validation_alias="STATIC_REVIEW_VALIDATION_CONFIDENCE_THRESHOLD", default=0.8, ge=0, le=1),
    ]
    gemini_api_key: Annotated[str, Field(validation_alias="GEMINI_API_KEY", default="")]

    @property
    def cors_origins(self) -> list[str]:
        return [self.frontend_url]

    @property
    def allowed_github_logins(self) -> frozenset[str]:
        return frozenset(login.strip().lower() for login in self.auth_allowed_github_logins.split(",") if login.strip())

    @property
    def github_oauth_configured(self) -> bool:
        return bool(self.github_app_client_id.strip() and self.github_app_client_secret.get_secret_value().strip())

    @field_validator("github_oauth_callback_url")
    @classmethod
    def validate_callback_url(cls, value: str) -> str:
        from urllib.parse import urlparse
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.query or parsed.fragment:
            raise ValueError("GITHUB_OAUTH_CALLBACK_URL must be an absolute origin path.")
        return value

    @model_validator(mode="after")
    def validate_static_review_limits(self) -> "Settings":
        if self.static_review_max_total_bytes < self.static_review_max_file_bytes:
            raise ValueError("STATIC_REVIEW_MAX_TOTAL_BYTES must be at least STATIC_REVIEW_MAX_FILE_BYTES")
        if self.app_env != "development" and not self.auth_cookie_secure:
            raise ValueError("AUTH_COOKIE_SECURE must be enabled outside development.")
        if self.app_env == "development" and not self.allowed_github_logins:
            raise ValueError("AUTH_ALLOWED_GITHUB_LOGINS is required in development.")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
