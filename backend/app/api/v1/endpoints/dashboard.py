from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.read_dependencies import read_session
from app.api.v1.auth_dependencies import get_current_user
from app.repositories.dashboard import dashboard_statistics
from app.schemas.dashboard import DashboardStatistics

router = APIRouter(prefix="/dashboard", tags=["dashboard"], dependencies=[Depends(get_current_user)])


@router.get("/statistics", response_model=DashboardStatistics)
async def statistics(session: Annotated[AsyncSession, Depends(read_session)]) -> DashboardStatistics:
    return await dashboard_statistics(session)
