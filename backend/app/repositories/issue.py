from datetime import datetime
from uuid import UUID

from sqlalchemy import Select, String, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import GitHubIssue, Repository
from app.schemas.github import GitHubIssue as GitHubIssueData
from app.schemas.issue import IssueResponse
from app.schemas.pagination import Page, PageParams, paginated


class IssueStore:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert(self, repository_id: UUID, data: GitHubIssueData, synced_at: datetime) -> None:
        values = data.model_dump()
        await self.session.execute(
            insert(GitHubIssue).values(**values, repository_id=repository_id, last_synced_at=synced_at)
            .on_conflict_do_update(index_elements=[GitHubIssue.repository_id, GitHubIssue.github_issue_number], set_={**values, "last_synced_at": synced_at})
        )

    @staticmethod
    def _response(issue: GitHubIssue, repository: Repository) -> IssueResponse:
        return IssueResponse.model_validate(issue).model_copy(update={"repository_full_name": repository.full_name})

    async def get(self, issue_id: UUID) -> IssueResponse | None:
        row = (await self.session.execute(select(GitHubIssue, Repository).join(Repository).where(GitHubIssue.id == issue_id))).one_or_none()
        return self._response(*row) if row else None

    async def list(self, params: PageParams, repository_id: UUID | None = None, state: str | None = None, search: str | None = None, author: str | None = None, assignee: str | None = None, label: str | None = None) -> Page[IssueResponse]:
        filters = []
        if repository_id is not None:
            filters.append(GitHubIssue.repository_id == repository_id)
        if state is not None:
            filters.append(GitHubIssue.state == state)
        if search:
            filters.append(GitHubIssue.title.icontains(search, autoescape=True))
        if author:
            filters.append(GitHubIssue.author_login.icontains(author, autoescape=True))
        if assignee:
            filters.append(GitHubIssue.assignees.cast(String).icontains(assignee, autoescape=True))
        if label:
            filters.append(GitHubIssue.labels.cast(String).icontains(label, autoescape=True))
        total = (await self.session.execute(select(func.count()).select_from(GitHubIssue).where(*filters))).scalar_one()
        rows = (await self.session.execute(select(GitHubIssue, Repository).join(Repository).where(*filters).order_by(GitHubIssue.github_updated_at.desc(), GitHubIssue.id).offset((params.page - 1) * params.page_size).limit(params.page_size))).all()
        return paginated([self._response(*row) for row in rows], total, params)