from pydantic import BaseModel, ConfigDict

from app.core.config import settings


class HealthResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: str
    service: str
    version: str
    environment: str


def get_health() -> HealthResponse:
    return HealthResponse(
        status="healthy",
        service="ai-code-review-assistant-api",
        version=settings.app_version,
        environment=settings.app_env,
    )
