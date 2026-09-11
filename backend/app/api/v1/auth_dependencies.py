from typing import Annotated

from fastapi import Cookie, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db_session
from app.repositories.auth import AuthStore
from app.schemas.auth import AuthenticatedUser
from app.services.github.oauth import state_hash


async def get_current_user(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    token: Annotated[str | None, Cookie(alias=settings.auth_session_cookie_name)] = None,
) -> AuthenticatedUser:
    if not token:
        raise HTTPException(401, "Authentication required.")
    record = await AuthStore(session).current_session(state_hash(token))
    if record is None:
        raise HTTPException(401, "Authentication required.")
    return AuthenticatedUser(
        id=record.user.id,
        github_user_id=record.user.github_user_id,
        github_login=record.user.github_login,
        display_name=record.user.display_name,
        email=record.user.email,
        avatar_url=record.user.avatar_url,
        profile_url=record.user.profile_url,
        session_expires_at=record.expires_at,
    )
