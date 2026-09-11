from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import GitHubOAuthTransaction, User, UserSession
from app.schemas.auth import GitHubIdentity


class AuthStore:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_transaction(self, state_hash: str, verifier: str, next_path: str | None, expires_at: datetime) -> None:
        self.session.add(GitHubOAuthTransaction(state_hash=state_hash, code_verifier=verifier, next_path=next_path, expires_at=expires_at))
        await self.session.flush()

    async def consume_transaction(self, state_hash: str) -> GitHubOAuthTransaction | None:
        record = (await self.session.execute(select(GitHubOAuthTransaction).where(GitHubOAuthTransaction.state_hash == state_hash).with_for_update())).scalar_one_or_none()
        if record is None or record.consumed_at is not None or record.expires_at <= datetime.now(UTC):
            return None
        record.consumed_at = datetime.now(UTC)
        await self.session.flush()
        return record

    async def remove_expired_transactions(self) -> None:
        await self.session.execute(delete(GitHubOAuthTransaction).where(GitHubOAuthTransaction.expires_at < datetime.now(UTC)))

    async def upsert_user(self, identity: GitHubIdentity) -> User:
        record = (await self.session.execute(select(User).where(User.github_user_id == identity.github_user_id).with_for_update())).scalar_one_or_none()
        normalized = identity.login.lower()
        if record is None:
            record = User(github_user_id=identity.github_user_id, github_login=identity.login, github_login_normalized=normalized)
            self.session.add(record)
        record.github_login = identity.login
        record.github_login_normalized = normalized
        record.display_name = identity.display_name
        record.email = identity.email
        record.avatar_url = str(identity.avatar_url) if identity.avatar_url else None
        record.profile_url = str(identity.profile_url) if identity.profile_url else None
        record.last_login_at = datetime.now(UTC)
        await self.session.flush()
        return record

    async def create_session(self, user: User, token_hash: str, ttl_seconds: int) -> UserSession:
        now = datetime.now(UTC)
        record = UserSession(user_id=user.id, token_hash=token_hash, expires_at=now + timedelta(seconds=ttl_seconds), last_seen_at=now)
        self.session.add(record)
        await self.session.flush()
        return record

    async def current_session(self, token_hash: str) -> UserSession | None:
        return (await self.session.execute(select(UserSession).options(selectinload(UserSession.user)).join(User).where(
            UserSession.token_hash == token_hash,
            UserSession.revoked_at.is_(None),
            UserSession.expires_at > datetime.now(UTC),
            User.is_active.is_(True),
        ))).scalar_one_or_none()

    async def revoke_session(self, token_hash: str) -> None:
        record = (await self.session.execute(select(UserSession).where(UserSession.token_hash == token_hash).with_for_update())).scalar_one_or_none()
        if record is not None and record.revoked_at is None:
            record.revoked_at = datetime.now(UTC)
            await self.session.flush()
