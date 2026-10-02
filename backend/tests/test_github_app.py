import asyncio
import base64
import json
from datetime import UTC, datetime, timedelta

import httpx
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from app.clients.github_app import GitHubAppClient, app_jwt
from app.core.config import Settings


def write_key(path):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    path.write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))


def test_app_jwt_has_short_lived_claims_without_exposing_token(tmp_path):
    key_path = tmp_path / "app.pem"
    write_key(key_path)
    settings = Settings(_env_file=None, GITHUB_APP_ID="123", GITHUB_APP_PRIVATE_KEY_PATH=str(key_path))
    token = app_jwt(settings, now=datetime(2026, 1, 1, tzinfo=UTC))
    payload = json.loads(base64.urlsafe_b64decode(token.split(".")[1] + "=="))
    assert payload["iss"] == "123"
    assert payload["exp"] - payload["iat"] == 540


def test_installation_token_is_cached_until_refresh_skew(tmp_path):
    key_path = tmp_path / "app.pem"
    write_key(key_path)
    settings = Settings(_env_file=None, GITHUB_APP_ID="123", GITHUB_APP_PRIVATE_KEY_PATH=str(key_path))
    calls = []

    def handler(request):
        calls.append(request.url.path)
        return httpx.Response(201, json={"token": "short-lived-token", "expires_at": (datetime.now(UTC) + timedelta(hours=1)).isoformat()})

    async def run():
        async with GitHubAppClient(settings, transport=httpx.MockTransport(handler)) as client:
            first = await client.installation_token(42)
            second = await client.installation_token(42)
            third = await client.installation_token(43)
            assert first.value == second.value
            assert third.value == first.value

    asyncio.run(run())
    assert calls == ["/app/installations/42/access_tokens", "/app/installations/43/access_tokens"]