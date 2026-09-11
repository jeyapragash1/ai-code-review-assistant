from __future__ import annotations

import base64
import hashlib
import secrets
from urllib.parse import urlencode

import httpx

from app.schemas.auth import GitHubIdentity


class OAuthError(Exception):
    pass


def generate_state() -> str:
    return secrets.token_urlsafe(32)


def state_hash(state: str) -> str:
    return hashlib.sha256(state.encode("utf-8")).hexdigest()


def generate_verifier() -> str:
    return secrets.token_urlsafe(64)[:128]


def code_challenge(verifier: str) -> str:
    return base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("ascii")).digest()).rstrip(b"=").decode("ascii")


def safe_next_path(value: str | None) -> str | None:
    if not value or not value.startswith("/") or value.startswith("//") or "\\" in value or "%" in value or any(ord(char) < 32 for char in value):
        return None
    return value


class GitHubOAuthClient:
    authorize_url = "https://github.com/login/oauth/authorize"
    token_url = "https://github.com/login/oauth/access_token"
    user_url = "https://api.github.com/user"

    def __init__(self, client_id: str, client_secret: str, callback_url: str, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self.client_id, self.client_secret, self.callback_url, self.transport = client_id, client_secret, callback_url, transport

    def authorization_url(self, state: str, verifier: str) -> str:
        return self.authorize_url + "?" + urlencode({"client_id": self.client_id, "redirect_uri": self.callback_url, "state": state, "code_challenge": code_challenge(verifier), "code_challenge_method": "S256"})

    async def identity_from_code(self, code: str, verifier: str) -> GitHubIdentity:
        timeout = httpx.Timeout(15)
        async with httpx.AsyncClient(timeout=timeout, transport=self.transport) as client:
            try:
                token_response = await client.post(self.token_url, headers={"Accept": "application/json"}, data={"client_id": self.client_id, "client_secret": self.client_secret, "code": code, "redirect_uri": self.callback_url, "code_verifier": verifier})
                if token_response.status_code != 200 or "application/json" not in token_response.headers.get("content-type", ""):
                    raise OAuthError()
                token = token_response.json().get("access_token")
                if not isinstance(token, str) or not token:
                    raise OAuthError()
                user_response = await client.get(self.user_url, headers={"Accept": "application/vnd.github+json", "Authorization": f"Bearer {token}", "X-GitHub-Api-Version": "2022-11-28"})
                if user_response.status_code != 200 or "application/json" not in user_response.headers.get("content-type", ""):
                    raise OAuthError()
                payload = user_response.json()
            except (httpx.HTTPError, ValueError, OAuthError) as error:
                raise OAuthError() from error
        try:
            return GitHubIdentity(github_user_id=payload["id"], login=payload["login"], display_name=payload.get("name"), email=payload.get("email"), avatar_url=payload.get("avatar_url"), profile_url=payload.get("html_url"))
        except (KeyError, TypeError, ValueError) as error:
            raise OAuthError() from error
