from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.repositories.pull_request import PullRequestStore
from app.repositories.repository import RepositoryStore


async def read_session(session: Annotated[AsyncSession, Depends(get_db_session)]) -> AsyncIterator[AsyncSession]:
    try:
        yield session
    except SQLAlchemyError:
        try:
            await session.rollback()
        finally:
            raise HTTPException(503, "Data is temporarily unavailable.") from None


def repository_store(session: Annotated[AsyncSession, Depends(read_session)]) -> RepositoryStore:
    return RepositoryStore(session)


def pull_request_store(session: Annotated[AsyncSession, Depends(read_session)]) -> PullRequestStore:
    return PullRequestStore(session)
