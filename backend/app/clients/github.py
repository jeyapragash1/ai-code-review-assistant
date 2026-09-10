import asyncio
import math
import re
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from urllib.parse import parse_qs, urlsplit

import httpx
from pydantic import TypeAdapter, ValidationError

from app.core.config import Settings
from app.clients.errors import GitHubError, GitHubRateLimitError
from app.schemas.github import GitHubPullRequest, GitHubRepository, PullRequestReference, RepositoryTarget


def usable_token(value: str) -> str | None:
    value = value.strip()
    if not value or value.lower().startswith(("replace", "your", "placeholder", "example", "changeme", "dummy", "<")):
        return None
    if not re.fullmatch(r"[A-Za-z0-9_]+", value):
        raise GitHubError("GitHub authentication configuration is invalid.")
    return value


class GitHubClient:
    def __init__(self, settings: Settings, *, transport: httpx.AsyncBaseTransport | None = None) -> None:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": settings.github_api_version,
            "User-Agent": "ai-code-review-assistant/0.1.0",
        }
        token = usable_token(settings.github_token)
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self._client = httpx.AsyncClient(
            base_url=settings.github_api_base_url,
            headers=headers,
            timeout=httpx.Timeout(settings.github_request_timeout_seconds, connect=min(5, settings.github_request_timeout_seconds)),
            follow_redirects=False,
            transport=transport,
        )
        self._retries = settings.github_max_retries

    async def __aenter__(self) -> "GitHubClient":
        return self

    async def __aexit__(self, *_: object) -> None:
        await self._client.aclose()

    async def _get(self, path: str, params: dict[str, str | int] | None = None) -> httpx.Response:
        for attempt in range(self._retries + 1):
            try:
                response = await self._client.get(path, params=params)
            except (httpx.TimeoutException, httpx.NetworkError):
                if attempt == self._retries:
                    raise GitHubError("GitHub is temporarily unavailable.") from None
                await asyncio.sleep(min(2**attempt, 5))
                continue
            except httpx.HTTPError:
                raise GitHubError("GitHub request failed.") from None
            if response.status_code == 200:
                return response
            rate_limited = response.status_code == 429 or (
                response.status_code == 403 and (
                    response.headers.get("x-ratelimit-remaining") == "0" or "retry-after" in response.headers
                )
            )
            if response.status_code == 403 and not rate_limited:
                try:
                    body = response.json()
                    message = body.get("message", "") if isinstance(body, dict) else ""
                    rate_limited = isinstance(message, str) and "rate limit" in message.lower()
                except ValueError:
                    pass
            transient = response.status_code in {429, 500, 502, 503, 504}
            if not transient or attempt == self._retries:
                if rate_limited:
                    raise GitHubRateLimitError("GitHub rate limit reached; retry later.")
                raise GitHubError("GitHub request could not be completed.")
            delay = self._retry_delay(response, attempt)
            # Long server-directed waits abort the run rather than retrying prematurely.
            if delay > 5:
                if rate_limited:
                    raise GitHubRateLimitError("GitHub rate limit reached; retry later.")
                raise GitHubError("GitHub requested a later retry.")
            await asyncio.sleep(delay)
        raise GitHubError("GitHub request failed.")

    @staticmethod
    def _retry_delay(response: httpx.Response, attempt: int) -> float:
        value = response.headers.get("retry-after")
        if value:
            try:
                delay = float(value)
                if math.isfinite(delay):
                    return max(0, delay)
            except ValueError:
                try:
                    return max(0, (parsedate_to_datetime(value) - datetime.now(UTC)).total_seconds())
                except (ValueError, TypeError, OverflowError):
                    pass
        return min(2**attempt, 5)

    async def repository(self, target: RepositoryTarget) -> GitHubRepository:
        response = await self._get(f"/repos/{target.owner}/{target.repo}")
        try:
            data = GitHubRepository.model_validate_json(response.content)
            if data.full_name.lower() != f"{target.owner}/{target.repo}".lower():
                raise ValueError("Unexpected repository")
            return data
        except (ValidationError, ValueError):
            raise GitHubError("GitHub returned invalid repository metadata.") from None

    async def pull_requests(self, target: RepositoryTarget) -> list[GitHubPullRequest]:
        path = f"/repos/{target.owner}/{target.repo}/pulls"
        page = 1
        numbers: set[int] = set()
        items: list[GitHubPullRequest] = []
        while True:
            response = await self._get(path, {"state": "all", "sort": "updated", "direction": "desc", "per_page": 100, "page": page})
            try:
                refs = TypeAdapter(list[PullRequestReference]).validate_json(response.content)
            except ValidationError:
                raise GitHubError("GitHub returned invalid pull request metadata.") from None
            # Sequential detail reads bound concurrency to one and avoid secondary rate limits.
            for ref in refs:
                if ref.number in numbers:
                    continue
                detail = await self._get(f"{path}/{ref.number}")
                try:
                    item = GitHubPullRequest.model_validate_json(detail.content)
                    if item.github_pr_number != ref.number:
                        raise ValueError("Unexpected pull request")
                except (ValidationError, ValueError):
                    raise GitHubError("GitHub returned invalid pull request details.") from None
                numbers.add(ref.number)
                items.append(item)
            next_url = response.links.get("next", {}).get("url")
            if not next_url:
                return items
            try:
                url = urlsplit(next_url)
                query = parse_qs(url.query, strict_parsing=True)
                next_page = int(query["page"][0])
                if url.scheme != "https" or url.netloc != "api.github.com" or url.path != path or url.fragment or next_page != page + 1:
                    raise ValueError("Invalid pagination")
                if len(query["page"]) != 1:
                    raise ValueError("Invalid pagination")
            except (ValueError, KeyError):
                raise GitHubError("GitHub returned invalid pagination.") from None
            page = next_page
