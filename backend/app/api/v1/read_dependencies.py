from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.repositories.pull_request import PullRequestStore
from app.repositories.repository import RepositoryStore
from app.repositories.review import ReviewFindingStore, ReviewStore
from app.repositories.issue import IssueStore
from app.repositories.commit import CommitStore
from app.api.v1.auth_dependencies import get_current_user
from app.api.v1.scoped_session import ScopedReadSession
from app.schemas.auth import AuthenticatedUser


async def read_session(session: Annotated[AsyncSession, Depends(get_db_session)], user: Annotated[AuthenticatedUser, Depends(get_current_user)]) -> AsyncIterator[AsyncSession]:
    try:
        yield ScopedReadSession(session, user)
    except SQLAlchemyError:
        try:
            await session.rollback()
        finally:
            raise HTTPException(503, "Data is temporarily unavailable.") from None


def repository_store(session: Annotated[AsyncSession, Depends(read_session)]) -> RepositoryStore:
    return RepositoryStore(session)


def pull_request_store(session: Annotated[AsyncSession, Depends(read_session)]) -> PullRequestStore:
    return PullRequestStore(session)


def review_store(session: Annotated[AsyncSession, Depends(read_session)]) -> ReviewStore:
    return ReviewStore(session)


def review_finding_store(session: Annotated[AsyncSession, Depends(read_session)]) -> ReviewFindingStore:
    return ReviewFindingStore(session)


def issue_store(session: Annotated[AsyncSession, Depends(read_session)]) -> IssueStore:
    return IssueStore(session)


def commit_store(session: Annotated[AsyncSession, Depends(read_session)]) -> CommitStore:
    return CommitStore(session)
