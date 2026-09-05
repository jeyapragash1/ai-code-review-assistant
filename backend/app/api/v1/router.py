from fastapi import APIRouter

from app.api.v1.endpoints.health import HealthResponse, get_health

api_router = APIRouter()


@api_router.get("/health", response_model=HealthResponse, tags=["health"])
def health_check() -> HealthResponse:
    return get_health()
