import asyncio
import base64
from unittest.mock import AsyncMock

import httpx
import pytest
from pydantic import ValidationError

from app.clients.github import GitHubClient, GitHubError, GitHubRateLimitError
from app.core.config import Settings
from app.schemas.github import GitHubPullRequest, GitHubRepository, RepositoryTarget
from tests.github_fixtures import pr_payload, repository_payload

TARGET = RepositoryTarget(owner="octocat", repo="example")


def settings(token: str = "") -> Settings:
    return Settings(_env_file=None, GITHUB_TOKEN=token)


@pytest.mark.parametrize("token,authorized", [("", False), ("replace-with-github-token", False), ("  ", False), ("your-github-token", False), ("valid_test_token", True)])
def test_headers_and_optional_authentication(token, authorized, caplog):
    def handler(request):
        assert request.headers["Accept"] == "application/vnd.github+json"
        assert request.headers["X-GitHub-Api-Version"] == "2026-03-10"
        assert request.headers["User-Agent"].startswith("ai-code-review-assistant/")
        assert ("Authorization" in request.headers) is authorized
        if authorized:
            assert request.headers["Authorization"] == f"Bearer {token}"
        return httpx.Response(200, json=repository_payload())
    async def run():
        async with GitHubClient(settings(token), transport=httpx.MockTransport(handler)) as client:
            result = await client.repository(TARGET)
            assert result.github_repository_id == 101
            assert result.owner == "octocat"
            assert result.primary_language == "Python"
            assert result.github_updated_at.tzinfo is not None
    asyncio.run(run())
    assert "valid_test_token" not in caplog.text


@pytest.mark.parametrize("state,merged,expected", [("open", None, "open"), ("closed", None, "closed"), ("closed", "2026-09-01T12:00:00Z", "merged")])
def test_state_normalization(state, merged, expected):
    result = GitHubPullRequest.model_validate(pr_payload(state=state, merged_at=merged))
    assert result.status.value == expected
    assert result.model_dump()["status"] == expected
    assert "state" not in result.model_dump()


def test_multiple_pages_and_accurate_detail_statistics():
    requests = []
    def handler(request):
        requests.append(request)
        if request.url.path.endswith("/pulls"):
            assert request.url.params["state"] == "all"
            assert request.url.params["sort"] == "updated"
            assert request.url.params["direction"] == "desc"
            if request.url.params["page"] == "1":
                return httpx.Response(200, json=[{"number": 1}], headers={"Link": '<https://api.github.com/repos/octocat/example/pulls?page=2>; rel="next"'})
            return httpx.Response(200, json=[{"number": 1}, {"number": 2}])
        return httpx.Response(200, json=pr_payload(int(request.url.path.rsplit("/", 1)[1])))
    async def run():
        async with GitHubClient(settings(), transport=httpx.MockTransport(handler)) as client:
            data = await client.pull_requests(TARGET)
            assert [pr.github_pr_number for pr in data] == [1, 2]
            assert data[0].additions == 10
            assert data[0].changed_files == 3
    asyncio.run(run())
    assert len(requests) == 4


@pytest.mark.parametrize("status", [429, 500, 502, 503, 504])
def test_transient_retries(status, monkeypatch):
    sleep = AsyncMock()
    monkeypatch.setattr("app.clients.github.asyncio.sleep", sleep)
    calls = 0
    def handler(request):
        nonlocal calls
        calls += 1
        return httpx.Response(status, headers={"Retry-After": "0"}) if calls == 1 else httpx.Response(200, json=repository_payload())
    async def run():
        async with GitHubClient(settings(), transport=httpx.MockTransport(handler)) as client:
            await client.repository(TARGET)
    asyncio.run(run())
    assert calls == 2
    sleep.assert_awaited_once_with(0)


@pytest.mark.parametrize("status", [401, 403, 404, 422, 301])
def test_nonretryable_errors_are_safe(status):
    calls = 0
    def handler(request):
        nonlocal calls
        calls += 1
        return httpx.Response(status, json={"message": "private upstream content"}, headers={"Location": "https://other.example/"})
    async def run():
        async with GitHubClient(settings(), transport=httpx.MockTransport(handler)) as client:
            with pytest.raises(GitHubError) as error:
                await client.repository(TARGET)
            assert "private upstream content" not in str(error.value)
    asyncio.run(run())
    assert calls == 1


@pytest.mark.parametrize("status,headers", [(403, {"x-ratelimit-remaining": "0"}), (429, {"Retry-After": "60"})])
def test_rate_limits_do_not_sleep_for_long_delays(status, headers, monkeypatch):
    sleep = AsyncMock()
    monkeypatch.setattr("app.clients.github.asyncio.sleep", sleep)
    async def run():
        async with GitHubClient(settings(), transport=httpx.MockTransport(lambda _: httpx.Response(status, headers=headers))) as client:
            with pytest.raises(GitHubRateLimitError):
                await client.repository(TARGET)
    asyncio.run(run())
    sleep.assert_not_awaited()


def test_retries_are_bounded(monkeypatch):
    sleep = AsyncMock()
    monkeypatch.setattr("app.clients.github.asyncio.sleep", sleep)
    calls = 0
    def handler(request):
        nonlocal calls
        calls += 1
        return httpx.Response(503)
    async def run():
        async with GitHubClient(settings(), transport=httpx.MockTransport(handler)) as client:
            with pytest.raises(GitHubError):
                await client.repository(TARGET)
    asyncio.run(run())
    assert calls == 4


@pytest.mark.parametrize("link", ["https://evil.example/repos/octocat/example/pulls?page=2", "https://api.github.com/other?page=2", "https://api.github.com/repos/octocat/example/pulls?page=1"])
def test_untrusted_pagination_is_rejected(link):
    async def run():
        async with GitHubClient(settings("valid_test_token"), transport=httpx.MockTransport(lambda _: httpx.Response(200, json=[], headers={"Link": f'<{link}>; rel="next"'}))) as client:
            with pytest.raises(GitHubError, match="pagination"):
                await client.pull_requests(TARGET)
    asyncio.run(run())


def test_changed_file_pagination_and_exact_head_content():
    seen = []
    content = base64.b64encode(b"print('safe to parse only')\n").decode()

    def handler(request):
        seen.append((request.url.path, dict(request.url.params)))
        if request.url.path.endswith("/pulls/1/files"):
            assert request.url.params["per_page"] == "100"
            if request.url.params["page"] == "1":
                return httpx.Response(
                    200,
                    json=[{"filename": "old.py", "status": "removed", "additions": 0, "deletions": 2, "changes": 2}],
                    headers={"Link": '<https://api.github.com/repos/octocat/example/pulls/1/files?page=2>; rel="next"'},
                )
            return httpx.Response(200, json=[{
                "filename": "src/new.py",
                "previous_filename": "src/old.py",
                "status": "renamed",
                "additions": 1,
                "deletions": 0,
                "changes": 1,
                "patch": "@@ -0,0 +1 @@",
            }])
        if request.url.path.endswith("/contents/src/new.py"):
            assert request.url.params["ref"] == "a" * 40
            return httpx.Response(200, json={"type": "file", "encoding": "base64", "size": 28, "content": content})
        return httpx.Response(404)

    async def run():
        async with GitHubClient(settings(), transport=httpx.MockTransport(handler)) as client:
            files = await client.pull_request_files(TARGET, 1, "a" * 40)
            assert [item.filename for item in files] == ["old.py", "src/new.py"]
            assert files[1].previous_filename == "src/old.py"
            assert files[1].head_sha == "a" * 40
            assert await client.file_content(TARGET, "src/new.py", "a" * 40, 100) == b"print('safe to parse only')\n"

    asyncio.run(run())
    assert seen[0][0] == "/repos/octocat/example/pulls/1/files"


def test_invalid_changed_file_metadata_is_safe():
    async def run():
        async with GitHubClient(settings(), transport=httpx.MockTransport(lambda _: httpx.Response(200, json=[{"filename": "", "status": "modified"}]))) as client:
            with pytest.raises(GitHubError, match="file metadata"):
                await client.pull_request_files(TARGET, 1, "a" * 40)
    asyncio.run(run())


def test_invalid_content_metadata_is_safe():
    async def run():
        async with GitHubClient(settings(), transport=httpx.MockTransport(lambda _: httpx.Response(200, json={"type": "symlink", "size": 1}))) as client:
            with pytest.raises(GitHubError, match="unsupported file content"):
                await client.file_content(TARGET, "src/app.py", "a" * 40, 100)
    asyncio.run(run())


@pytest.mark.parametrize("owner,repo", [("../bad", "good"), ("good", "../bad"), ("good", "a/b"), ("good", "a?token=x")])
def test_target_validation(owner, repo):
    with pytest.raises(ValidationError):
        RepositoryTarget(owner=owner, repo=repo)


def test_untrusted_base_url_is_rejected():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, github_api_base_url="https://other.example")


@pytest.mark.parametrize("changes", [{"additions": -1}, {"changed_files": True}, {"deletions": "4"}, {"html_url": "http://evil.example"}, {"updated_at": "2026-09-01T00:00:00"}])
def test_invalid_upstream_values(changes):
    with pytest.raises(ValidationError):
        GitHubPullRequest.model_validate(pr_payload(**changes))


def test_invalid_repository_identity():
    with pytest.raises(ValidationError):
        GitHubRepository.model_validate(repository_payload() | {"full_name": "other/repo"})


def test_malformed_json_is_safe():
    async def run():
        async with GitHubClient(settings(), transport=httpx.MockTransport(lambda _: httpx.Response(200, content=b"not json"))) as client:
            with pytest.raises(GitHubError, match="invalid repository"):
                await client.repository(TARGET)
    asyncio.run(run())


def test_secondary_rate_limit_is_classified_without_exposing_body():
    async def run():
        async with GitHubClient(settings(), transport=httpx.MockTransport(lambda _: httpx.Response(403, json={"message": "secondary rate limit: private diagnostic"}))) as client:
            with pytest.raises(GitHubRateLimitError) as error:
                await client.repository(TARGET)
            assert "private diagnostic" not in str(error.value)
    asyncio.run(run())


def test_network_timeout_retries_are_bounded(monkeypatch):
    sleep = AsyncMock()
    monkeypatch.setattr("app.clients.github.asyncio.sleep", sleep)
    calls = 0
    def handler(request):
        nonlocal calls
        calls += 1
        raise httpx.ReadTimeout("private request details", request=request)
    async def run():
        async with GitHubClient(settings(), transport=httpx.MockTransport(handler)) as client:
            with pytest.raises(GitHubError, match="temporarily unavailable"):
                await client.repository(TARGET)
    asyncio.run(run())
    assert calls == 4
