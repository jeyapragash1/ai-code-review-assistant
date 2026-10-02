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
from app.api.v1.endpoints.issues import router as issues_router
from app.api.v1.endpoints.github import router as github_router
from app.api.v1.endpoints.commits import router as commits_router
from app.api.v1.endpoints.activity import router as activity_router
from app.api.v1.endpoints.review_jobs import router as review_jobs_router
from app.api.v1.endpoints.account_dashboard import router as account_dashboard_router
from app.db.health import check_database_connection
from app.db.session import get_db_session

logger = logging.getLogger(__name__)

api_router = APIRouter()
api_router.include_router(webhooks_router)
api_router.include_router(auth_router)
api_router.include_router(issues_router)
api_router.include_router(github_router)
api_router.include_router(commits_router)
api_router.include_router(activity_router)
api_router.include_router(review_jobs_router)
api_router.include_router(account_dashboard_router)
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
