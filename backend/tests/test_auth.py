import asyncio

import httpx
import pytest

from app.services.github.oauth import GitHubOAuthClient, OAuthError, code_challenge, generate_state, generate_verifier, safe_next_path, state_hash
from fastapi.testclient import TestClient
from app.main import create_app


def test_pkce_state_and_safe_redirect_helpers():
    state = generate_state()
    verifier = generate_verifier()
    assert len(state_hash(state)) == 64
    assert len(code_challenge(verifier)) >= 43
    assert safe_next_path("/reviews?status=completed") == "/reviews?status=completed"
    for value in ("https://example.com", "//example.com", "/%2fexample", "/\\example"):
        assert safe_next_path(value) is None


def test_protected_routes_require_session_and_health_remains_public():
    with TestClient(create_app()) as client:
        assert client.get("/api/v1/repositories").status_code == 401
        assert client.get("/api/v1/health").status_code == 200
        response = client.get("/api/v1/auth/github/login")
        assert response.status_code == 503
        assert "secret" not in response.text.lower()


def test_authorization_url_uses_pkce_and_safe_parameters():
    client = GitHubOAuthClient("client-id", "not-a-secret", "http://localhost:8000/api/v1/auth/github/callback")
    state, verifier = generate_state(), generate_verifier()
    url = httpx.URL(client.authorization_url(state, verifier))
    assert url.host == "github.com"
    assert url.params["client_id"] == "client-id"
    assert url.params["state"] == state
    assert url.params["code_challenge"] == code_challenge(verifier)
    assert url.params["code_challenge_method"] == "S256"


def test_oauth_client_exchanges_code_and_discards_token_from_result():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("access_token"):
            assert request.url.host == "github.com"
            assert request.content and b"code_verifier=" in request.content
            return httpx.Response(200, headers={"content-type": "application/json"}, json={"access_token": "test-token-never-persisted"})
        assert request.headers["authorization"] == "Bearer test-token-never-persisted"
        return httpx.Response(200, headers={"content-type": "application/json"}, json={"id": 1, "login": "Jeyapragash1", "avatar_url": "https://avatars.githubusercontent.com/u/1", "html_url": "https://github.com/Jeyapragash1"})
    identity = asyncio.run(GitHubOAuthClient("id", "secret", "http://localhost:8000/api/v1/auth/github/callback", httpx.MockTransport(handler)).identity_from_code("code", generate_verifier()))
    assert identity.github_user_id == 1
    assert "token" not in identity.model_dump_json()


@pytest.mark.parametrize("token_response", [
    httpx.Response(500),
    httpx.Response(200, headers={"content-type": "text/plain"}, text="no"),
    httpx.Response(200, headers={"content-type": "application/json"}, json={}),
])
def test_oauth_client_rejects_unsafe_token_responses(token_response):
    def handler(_: httpx.Request) -> httpx.Response:
        return token_response
    with pytest.raises(OAuthError):
        asyncio.run(GitHubOAuthClient("id", "secret", "http://localhost/callback", httpx.MockTransport(handler)).identity_from_code("code", generate_verifier()))
