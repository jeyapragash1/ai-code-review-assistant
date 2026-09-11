from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class AuthenticatedUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    github_user_id: int
    github_login: str
    display_name: str | None
    email: str | None
    avatar_url: HttpUrl | None
    profile_url: HttpUrl | None
    session_expires_at: datetime


class GitHubIdentity(BaseModel):
    github_user_id: int = Field(ge=1)
    login: str = Field(min_length=1, max_length=255)
    display_name: str | None = Field(default=None, max_length=255)
    email: str | None = Field(default=None, max_length=320)
    avatar_url: HttpUrl | None = Field(default=None, max_length=2048)
    profile_url: HttpUrl | None = Field(default=None, max_length=2048)

    @field_validator("login")
    @classmethod
    def normalize_login(cls, value: str) -> str:
        if value.strip() != value:
            raise ValueError("Invalid login.")
        return value
