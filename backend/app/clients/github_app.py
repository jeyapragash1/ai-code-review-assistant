from __future__ import annotations

import asyncio
import base64
import json
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, TypeAdapter, ValidationError

from app.clients.errors import GitHubError, GitHubRateLimitError
from app.core.config import Settings


class GitHubAppConfigurationError(GitHubError):
    pass


class GitHubInstallationSummary(BaseModel):
    model_config = ConfigDict(extra="ignore", hide_input_in_errors=True)

    id: int = Field(gt=0)
    account: dict[str, Any]
    repository_selection: str = Field(min_length=1, max_length=32)
    permissions: dict[str, Any] = Field(default_factory=dict)
    events: list[str] = Field(default_factory=list)
    suspended_at: AwareDatetime | None = None
    created_at: AwareDatetime | None = None
    updated_at: AwareDatetime | None = None


class InstallationRepository(BaseModel):
    model_config = ConfigDict(extra="ignore", hide_input_in_errors=True)

    id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=100)
    full_name: str = Field(min_length=1, max_length=200)
    owner: dict[str, Any]
    private: bool
    fork: bool = False
    archived: bool = False
    disabled: bool = False
    default_branch: str | None = Field(default=None, max_length=255)
    html_url: str | None = None
    language: str | None = Field(default=None, max_length=100)
    stargazers_count: int = Field(default=0, ge=0)
    forks_count: int = Field(default=0, ge=0)
    open_issues_count: int = Field(default=0, ge=0)
    pushed_at: AwareDatetime | None = None
    updated_at: AwareDatetime | None = None


class InstallationRepositoriesPage(BaseModel):
    repositories: list[InstallationRepository]
    total_count: int = Field(ge=0)


@dataclass(frozen=True)
class InstallationToken:
    value: str
    expires_at: datetime


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def app_jwt(settings: Settings, *, now: datetime | None = None) -> str:
    if not settings.github_app_id.strip() or not settings.github_app_private_key_path.strip():
        raise GitHubAppConfigurationError("GitHub App authentication is not configured.")
    path = Path(settings.github_app_private_key_path)
    if not path.is_absolute() or not path.is_file():
        raise GitHubAppConfigurationError("GitHub App private key configuration is invalid.")
    current = now or datetime.now(UTC)
    issued_at = int(current.timestamp()) - 60
    expires_at = issued_at + 540
    try:
        key = serialization.load_pem_private_key(path.read_bytes(), password=None)
        header = _b64(json.dumps({"alg": "RS256", "typ": "JWT"}, separators=(",", ":")).encode())
        payload = _b64(json.dumps({"iat": issued_at, "exp": expires_at, "iss": settings.github_app_id.strip()}, separators=(",", ":")).encode())
        message = f"{header}.{payload}".encode("ascii")
        signature = key.sign(message, padding.PKCS1v15(), hashes.SHA256())
        return f"{header}.{payload}.{_b64(signature)}"
    except (OSError, ValueError, TypeError):
        raise GitHubAppConfigurationError("GitHub App private key configuration is invalid.") from None


class GitHubAppClient:
    def __init__(self, settings: Settings, *, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self._settings = settings
        self._transport = transport
        self._client = httpx.AsyncClient(
            base_url=settings.github_api_base_url,
            headers={"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": settings.github_api_version, "User-Agent": "ai-code-review-assistant/0.1.0"},
            timeout=httpx.Timeout(settings.github_request_timeout_seconds, connect=min(5, settings.github_request_timeout_seconds)),
            follow_redirects=False,
            transport=transport,
        )
        self._token: InstallationToken | None = None

    async def __aenter__(self) -> "GitHubAppClient":
        return self

    async def __aexit__(self, *_: object) -> None:
        await self._client.aclose()

    async def _request(self, method: str, path: str, *, token: str | None = None, params: dict[str, int] | None = None, json_body: dict[str, Any] | None = None) -> httpx.Response:
        headers = {"Authorization": f"Bearer {token or app_jwt(self._settings)}"}
        attempts = self._settings.github_max_retries if method == "GET" else 0
        for attempt in range(attempts + 1):
            try:
                response = await self._client.request(method, path, headers=headers, params=params, json=json_body)
            except (httpx.TimeoutException, httpx.NetworkError):
                if attempt >= attempts:
                    raise GitHubError("GitHub is temporarily unavailable.") from None
                await asyncio.sleep(min(2**attempt, 5))
                continue
            if response.status_code in {200, 201}:
                return response
            if response.status_code in {429, 500, 502, 503, 504} and attempt < attempts:
                await asyncio.sleep(min(2**attempt, 5))
                continue
            if response.status_code == 429 or response.headers.get("x-ratelimit-remaining") == "0":
                raise GitHubRateLimitError("GitHub rate limit reached; retry later.")
            raise GitHubError("GitHub App request could not be completed.")
        raise GitHubError("GitHub App request failed.")

    async def installations(self) -> list[GitHubInstallationSummary]:
        page, items = 1, []
        while True:
            response = await self._request("GET", "/app/installations", params={"per_page": 100, "page": page})
            try:
                values = TypeAdapter(list[GitHubInstallationSummary]).validate_json(response.content)
            except ValidationError:
                raise GitHubError("GitHub returned invalid installation metadata.") from None
            items.extend(values)
            if len(values) < 100:
                return items
            page += 1

    async def installation(self, installation_id: int) -> GitHubInstallationSummary:
        response = await self._request("GET", f"/app/installations/{installation_id}")
        try:
            return GitHubInstallationSummary.model_validate_json(response.content)
        except ValidationError:
            raise GitHubError("GitHub returned invalid installation metadata.") from None

    async def installation_token(self, installation_id: int) -> InstallationToken:
        now = datetime.now(UTC)
        if self._token and self._token.expires_at - timedelta(seconds=self._settings.github_installation_token_refresh_skew_seconds) > now:
            return self._token
        response = await self._request("POST", f"/app/installations/{installation_id}/access_tokens")
        try:
            data = response.json()
            token = data["token"]
            expires_at = TypeAdapter(AwareDatetime).validate_python(data["expires_at"])
            if not isinstance(token, str) or not token:
                raise ValueError()
            self._token = InstallationToken(token, expires_at)
            return self._token
        except (KeyError, TypeError, ValueError, ValidationError):
            raise GitHubError("GitHub returned invalid installation token metadata.") from None

    async def installation_repositories(self, installation_id: int) -> list[InstallationRepository]:
        token = (await self.installation_token(installation_id)).value
        page, items = 1, []
        while True:
            response = await self._request("GET", "/installation/repositories", token=token, params={"per_page": 100, "page": page})
            try:
                data = InstallationRepositoriesPage.model_validate_json(response.content)
            except ValidationError:
                raise GitHubError("GitHub returned invalid installation repository metadata.") from None
            items.extend(data.repositories)
            if len(data.repositories) < 100:
                return items
            page += 1