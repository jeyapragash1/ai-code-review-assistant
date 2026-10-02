from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import GitHubInstallation, InstallationRepositoryAccess, Repository


class GitHubInstallationStore:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert(self, values: dict, synced_at: datetime) -> GitHubInstallation:
        record = (await self.session.execute(select(GitHubInstallation).where(GitHubInstallation.github_installation_id == values["github_installation_id"]).with_for_update())).scalar_one_or_none()
        if record is None:
            record = GitHubInstallation(**values, last_synced_at=synced_at)
            self.session.add(record)
        else:
            for key, value in values.items():
                setattr(record, key, value)
            record.last_synced_at = synced_at
            record.is_active = True
        await self.session.flush()
        return record

    async def upsert_access(self, installation_id: UUID, repository_id: UUID, seen_at: datetime) -> InstallationRepositoryAccess:
        record = (await self.session.execute(select(InstallationRepositoryAccess).where(InstallationRepositoryAccess.installation_id == installation_id, InstallationRepositoryAccess.repository_id == repository_id).with_for_update())).scalar_one_or_none()
        if record is None:
            record = InstallationRepositoryAccess(installation_id=installation_id, repository_id=repository_id, first_seen_at=seen_at, last_seen_at=seen_at)
            self.session.add(record)
        else:
            record.last_seen_at = seen_at
            record.revoked_at = None
            record.is_active = True
        await self.session.flush()
        return record

    async def revoke_missing(self, installation_id: UUID, repository_ids: set[UUID], revoked_at: datetime) -> None:
        rows = (await self.session.execute(select(InstallationRepositoryAccess).where(InstallationRepositoryAccess.installation_id == installation_id, InstallationRepositoryAccess.is_active.is_(True)).with_for_update())).scalars().all()
        for row in rows:
            if row.repository_id not in repository_ids:
                row.is_active = False
                row.revoked_at = revoked_at