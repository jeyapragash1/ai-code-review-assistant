from typing import Annotated, Literal

from pydantic import AliasPath, AwareDatetime, BaseModel, ConfigDict, Field, computed_field, field_validator, model_validator

from app.models.enums import PullRequestStatus

PositiveID = Annotated[int, Field(strict=True, gt=0, le=2**63 - 1)]
Counter = Annotated[int, Field(strict=True, ge=0, le=2**31 - 1)]
Owner = Annotated[str, Field(pattern=r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$")]
RepoName = Annotated[str, Field(pattern=r"^[A-Za-z0-9_-][A-Za-z0-9_.-]{0,99}$")]


class RepositoryTarget(BaseModel):
    owner: Owner
    repo: RepoName


class GitHubData(BaseModel):
    model_config = ConfigDict(extra="ignore", hide_input_in_errors=True)

    @field_validator("html_url", check_fields=False)
    @classmethod
    def github_html_url(cls, value: str) -> str:
        from urllib.parse import urlsplit
        url = urlsplit(value)
        if url.scheme != "https" or url.netloc != "github.com" or url.username or url.fragment:
            raise ValueError("Invalid GitHub HTML URL")
        return value


class GitHubRepository(GitHubData):
    github_repository_id: PositiveID = Field(validation_alias="id")
    owner: Owner = Field(validation_alias=AliasPath("owner", "login"))
    name: RepoName
    full_name: str = Field(min_length=1, max_length=200)
    default_branch: str = Field(min_length=1, max_length=255)
    html_url: str = Field(max_length=2048)
    description: str | None = None
    primary_language: str | None = Field(default=None, validation_alias="language", max_length=100)
    is_private: bool = Field(validation_alias="private", strict=True)
    is_fork: bool = Field(validation_alias="fork", default=False, strict=True)
    is_archived: bool = Field(validation_alias="archived", default=False, strict=True)
    is_disabled: bool = Field(validation_alias="disabled", default=False, strict=True)
    stargazer_count: Counter = Field(validation_alias="stargazers_count", default=0)
    fork_count: Counter = Field(validation_alias="forks_count", default=0)
    open_issue_count: Counter = Field(validation_alias="open_issues_count", default=0)
    github_updated_at: AwareDatetime = Field(validation_alias="updated_at")
    github_pushed_at: AwareDatetime | None = Field(default=None, validation_alias="pushed_at")

    @model_validator(mode="after")
    def consistent_identity(self) -> "GitHubRepository":
        if self.full_name != f"{self.owner}/{self.name}":
            raise ValueError("Inconsistent repository identity")
        return self


class PullRequestReference(BaseModel):
    number: Annotated[int, Field(strict=True, gt=0, le=2**31 - 1)]


class GitHubPullRequest(GitHubData):
    github_pr_number: Annotated[int, Field(strict=True, gt=0, le=2**31 - 1)] = Field(validation_alias="number")
    title: str = Field(min_length=1, max_length=512)
    author_login: str = Field(validation_alias=AliasPath("user", "login"), min_length=1, max_length=255)
    base_branch: str = Field(validation_alias=AliasPath("base", "ref"), min_length=1, max_length=255)
    head_branch: str = Field(validation_alias=AliasPath("head", "ref"), min_length=1, max_length=255)
    head_sha: str = Field(validation_alias=AliasPath("head", "sha"), pattern=r"^[0-9a-fA-F]{40}$")
    html_url: str = Field(max_length=2048)
    state: Literal["open", "closed"] = Field(exclude=True)
    merged_at: AwareDatetime | None = Field(exclude=True)
    is_draft: bool = Field(validation_alias="draft", strict=True)
    additions: Counter
    deletions: Counter
    changed_files: Counter
    github_created_at: AwareDatetime = Field(validation_alias="created_at")
    github_updated_at: AwareDatetime = Field(validation_alias="updated_at")

    @computed_field
    @property
    def status(self) -> PullRequestStatus:
        if self.merged_at is not None:
            return PullRequestStatus.MERGED
        return PullRequestStatus.CLOSED if self.state == "closed" else PullRequestStatus.OPEN


class GitHubPullRequestFile(BaseModel):
    model_config = ConfigDict(extra="ignore", hide_input_in_errors=True)

    filename: str = Field(min_length=1, max_length=1024)
    status: Literal["added", "removed", "modified", "renamed", "copied", "changed", "unchanged"]
    additions: Counter
    deletions: Counter
    changes: Counter
    patch: str | None = None
    previous_filename: str | None = Field(default=None, max_length=1024)
    head_sha: str | None = Field(default=None, pattern=r"^[0-9a-fA-F]{40}$")


class GitHubIssue(BaseModel):
    model_config = ConfigDict(extra="ignore", hide_input_in_errors=True)

    github_issue_id: PositiveID = Field(validation_alias="id")
    github_issue_number: Annotated[int, Field(strict=True, gt=0, le=2**31 - 1)] = Field(validation_alias="number")
    title: str = Field(min_length=1, max_length=512)
    body: str | None = Field(default=None, max_length=100_000)
    state: Literal["open", "closed"]
    state_reason: str | None = Field(default=None, max_length=32)
    author_login: str | None = Field(default=None, validation_alias=AliasPath("user", "login"), max_length=255)
    author_github_id: PositiveID | None = Field(default=None, validation_alias=AliasPath("user", "id"))
    assignees: list[dict] = Field(default_factory=list)
    labels: list[dict] = Field(default_factory=list)
    is_locked: bool = Field(validation_alias="locked", default=False, strict=True)
    comment_count: Counter = Field(validation_alias="comments", default=0)
    html_url: str = Field(max_length=2048)
    github_created_at: AwareDatetime = Field(validation_alias="created_at")
    github_updated_at: AwareDatetime = Field(validation_alias="updated_at")
    github_closed_at: AwareDatetime | None = Field(default=None, validation_alias="closed_at")


def is_github_pull_request_issue(value: dict) -> bool:
    return isinstance(value.get("pull_request"), dict)


class GitHubCommit(BaseModel):
    model_config = ConfigDict(extra="ignore", hide_input_in_errors=True)

    sha: str = Field(pattern=r"^[0-9a-fA-F]{40}$")
    html_url: str | None = None
    commit: dict
    author: dict | None = None
    committer: dict | None = None
    parents: list[dict] = Field(default_factory=list)


class GitHubContentFile(BaseModel):
    model_config = ConfigDict(extra="ignore", hide_input_in_errors=True)

    type: Literal["file"]
    encoding: Literal["base64"]
    size: Counter
    content: str
