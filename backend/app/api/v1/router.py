import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.health import (
    HealthResponse,
    ReadinessResponse,
    ReadinessUnavailableResponse,
    get_health,
)
from app.api.v1.endpoints.webhooks import router as webhooks_router
from app.api.v1.endpoints.repositories import router as repositories_router
from app.api.v1.endpoints.pull_requests import router as pull_requests_router
from app.api.v1.endpoints.reviews import router as reviews_router
from app.api.v1.endpoints.dashboard import router as dashboard_router
from app.api.v1.endpoints.auth import router as auth_router
from app.db.health import check_database_connection
from app.db.session import get_db_session

logger = logging.getLogger(__name__)

api_router = APIRouter()
api_router.include_router(webhooks_router)
api_router.include_router(auth_router)
api_router.include_router(repositories_router)
api_router.include_router(pull_requests_router)
api_router.include_router(reviews_router)
api_router.include_router(dashboard_router)


@api_router.get("/health", response_model=HealthResponse, tags=["health"])
def health_check() -> HealthResponse:
    return get_health()


@api_router.get(
    "/health/ready",
    response_model=ReadinessResponse,
    responses={503: {"model": ReadinessUnavailableResponse}},
    tags=["health"],
)
async def readiness_check(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ReadinessResponse | JSONResponse:
    if await check_database_connection(session):
        return ReadinessResponse(status="ready", database="connected")

    logger.warning("Database readiness check failed.")
    return JSONResponse(
        status_code=503,
        content=ReadinessUnavailableResponse(
            status="not_ready",
            database="unavailable",
        ).model_dump(),
    )
