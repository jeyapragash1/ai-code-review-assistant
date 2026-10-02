import asyncio

import httpx

from app.clients.github import GitHubClient
from app.core.config import Settings
from app.schemas.github import RepositoryTarget


def issue_payload(number: int, *, pull_request: bool = False) -> dict:
    value = {
        "id": 900 + number,
        "number": number,
        "title": f"Issue {number}",
        "body": "body",
        "state": "open",
        "state_reason": "completed",
        "user": {"id": 10, "login": "octocat"},
        "assignees": [],
        "labels": [{"name": "bug", "color": "red"}],
        "locked": False,
        "comments": 2,
        "html_url": f"https://github.com/octocat/example/issues/{number}",
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-02T00:00:00Z",
        "closed_at": None,
    }
    if pull_request:
        value["pull_request"] = {"url": "https://api.github.com/repos/octocat/example/pulls/3"}
    return value


def test_issues_exclude_pull_requests_and_follow_pages():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["state"] == "all"
        if request.url.params["page"] == "1":
            return httpx.Response(200, json=[issue_payload(1), issue_payload(3, pull_request=True)], headers={"Link": '<https://api.github.com/repos/octocat/example/issues?page=2>; rel="next"'})
        return httpx.Response(200, json=[issue_payload(2)])

    async def run():
        async with GitHubClient(Settings(_env_file=None), transport=httpx.MockTransport(handler)) as client:
            result = await client.issues(RepositoryTarget(owner="octocat", repo="example"))
            assert [item.github_issue_number for item in result] == [1, 2]
            assert result[0].labels[0]["name"] == "bug"

    asyncio.run(run())
