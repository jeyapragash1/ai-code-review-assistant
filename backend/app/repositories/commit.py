from datetime import datetime
from uuid import UUID

from sqlalchemy import String, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import GitHubCommit, Repository
from app.schemas.commit import CommitResponse
from app.schemas.github import GitHubCommit as GitHubCommitData
from app.schemas.pagination import Page, PageParams, paginated


class CommitStore:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert(self, repository_id: UUID, data: GitHubCommitData, synced_at: datetime, reference: str | None) -> None:
        commit_data = data.commit
        author = data.author or {}
        committer = data.committer or {}
        values = {
            "repository_id": repository_id, "sha": data.sha, "title": str(commit_data.get("message", "")).splitlines()[0][:512] or data.sha,
            "message": commit_data.get("message"), "author_name": (commit_data.get("author") or {}).get("name"), "author_login": author.get("login"),
            "committer_name": (commit_data.get("committer") or {}).get("name"), "committer_login": committer.get("login"),
            "authored_at": (commit_data.get("author") or {}).get("date"), "committed_at": (commit_data.get("committer") or {}).get("date"),
            "html_url": data.html_url, "parent_count": len(data.parents), "reference": reference, "last_synced_at": synced_at,
        }
        await self.session.execute(insert(GitHubCommit).values(**values).on_conflict_do_update(index_elements=[GitHubCommit.repository_id, GitHubCommit.sha], set_={key: value for key, value in values.items() if key not in {"repository_id", "sha"}}))

    async def list(self, params: PageParams, repository_id: UUID | None = None) -> Page[CommitResponse]:
        filters = [GitHubCommit.repository_id == repository_id] if repository_id else []
        total = (await self.session.execute(select(func.count()).select_from(GitHubCommit).where(*filters))).scalar_one()
        rows = (await self.session.execute(select(GitHubCommit, Repository).join(Repository).where(*filters).order_by(GitHubCommit.authored_at.desc().nulls_last(), GitHubCommit.id).offset((params.page - 1) * params.page_size).limit(params.page_size))).all()
        return paginated([CommitResponse.model_validate(commit).model_copy(update={"repository_full_name": repository.full_name}) for commit, repository in rows], total, params)
