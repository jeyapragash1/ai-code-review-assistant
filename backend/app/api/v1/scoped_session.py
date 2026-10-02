from sqlalchemy import select
from sqlalchemy.orm import with_loader_criteria
from app.models import GitHubCommit, GitHubInstallation, GitHubIssue, InstallationRepositoryAccess, PullRequest, Repository, Review, ReviewFinding
from app.api.v1.access import owned_repository_ids


class ScopedReadSession:
    """Apply ownership constraints to all ORM reads, including aggregate queries."""
    def __init__(self, session, user):
        self.session = session
        ids = owned_repository_ids(user)
        prs = select(PullRequest.id).where(PullRequest.repository_id.in_(ids))
        reviews = select(Review.id).where(Review.pull_request_id.in_(prs))
        self.criteria = [
            with_loader_criteria(Repository, Repository.id.in_(ids), include_aliases=True),
            with_loader_criteria(PullRequest, PullRequest.repository_id.in_(ids), include_aliases=True),
            with_loader_criteria(GitHubIssue, GitHubIssue.repository_id.in_(ids), include_aliases=True),
            with_loader_criteria(GitHubCommit, GitHubCommit.repository_id.in_(ids), include_aliases=True),
            with_loader_criteria(Review, Review.pull_request_id.in_(prs), include_aliases=True),
            with_loader_criteria(ReviewFinding, ReviewFinding.review_id.in_(reviews), include_aliases=True),
        ]

    def __getattr__(self, name):
        return getattr(self.session, name)

    async def execute(self, statement, *args, **kwargs):
        if getattr(statement, "is_select", False):
            statement = statement.options(*self.criteria)
        return await self.session.execute(statement, *args, **kwargs)

    async def scalar(self, statement, *args, **kwargs):
        if getattr(statement, "is_select", False):
            statement = statement.options(*self.criteria)
        return await self.session.scalar(statement, *args, **kwargs)
