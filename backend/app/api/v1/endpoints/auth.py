from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth_dependencies import get_current_user
from app.core.config import settings
from app.db.session import get_db_session
from app.repositories.auth import AuthStore
from app.schemas.auth import AuthenticatedUser
from app.services.github.oauth import GitHubOAuthClient, OAuthError, generate_state, generate_verifier, safe_next_path, state_hash

router = APIRouter(prefix="/auth", tags=["authentication"])


def no_store(response: Response) -> Response:
    response.headers["Cache-Control"] = "no-store"
    return response


def login_error(code: str) -> RedirectResponse:
    response = RedirectResponse(f"{settings.frontend_url}/login?error={code}", status_code=302)
    return no_store(response)


def cookie_kwargs() -> dict[str, object]:
    return {"key": settings.auth_session_cookie_name, "httponly": True, "secure": settings.auth_cookie_secure, "samesite": settings.auth_cookie_samesite, "path": "/"}


@router.get("/github/login")
async def github_login(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    next_path: Annotated[str | None, Query(alias="next", max_length=2048)] = None,
) -> RedirectResponse:
    if not settings.github_oauth_configured:
        raise HTTPException(503, "Authentication is temporarily unavailable.")
    state, verifier = generate_state(), generate_verifier()
    store = AuthStore(session)
    await store.remove_expired_transactions()
    await store.create_transaction(state_hash(state), verifier, safe_next_path(next_path), datetime.now(UTC) + timedelta(seconds=settings.auth_oauth_state_ttl_seconds))
    await session.commit()
    client = GitHubOAuthClient(settings.github_app_client_id, settings.github_app_client_secret.get_secret_value(), settings.github_oauth_callback_url)
    return no_store(RedirectResponse(client.authorization_url(state, verifier), status_code=302))


@router.get("/github/callback")
async def github_callback(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    code: str | None = Query(default=None, min_length=1, max_length=2048),
    state: str | None = Query(default=None, min_length=1, max_length=512),
    error: str | None = Query(default=None, max_length=100),
) -> RedirectResponse:
    if error or not code or not state or not settings.github_oauth_configured:
        return login_error("oauth_failed")
    transaction = await AuthStore(session).consume_transaction(state_hash(state))
    if transaction is None:
        await session.rollback()
        return login_error("oauth_failed")
    try:
        identity = await GitHubOAuthClient(settings.github_app_client_id, settings.github_app_client_secret.get_secret_value(), settings.github_oauth_callback_url).identity_from_code(code, transaction.code_verifier)
    except OAuthError:
        await session.commit()
        return login_error("oauth_failed")
    if identity.login.lower() not in settings.allowed_github_logins:
        await session.commit()
        return login_error("access_denied")
    store = AuthStore(session)
    user = await store.upsert_user(identity)
    raw_token = generate_state()
    user_session = await store.create_session(user, state_hash(raw_token), settings.auth_session_ttl_seconds)
    await session.commit()
    response = RedirectResponse(settings.frontend_url + (transaction.next_path or "/dashboard"), status_code=302)
    response.set_cookie(value=raw_token, max_age=settings.auth_session_ttl_seconds, expires=user_session.expires_at, **cookie_kwargs())
    return no_store(response)


@router.get("/me", response_model=AuthenticatedUser)
async def me(current_user: Annotated[AuthenticatedUser, Depends(get_current_user)]) -> AuthenticatedUser:
    return current_user


@router.post("/logout", status_code=204)
async def logout(
    request: Request,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Response:
    origin = request.headers.get("origin")
    if origin and origin != settings.frontend_url:
        raise HTTPException(403, "Request origin is not allowed.")
    token = request.cookies.get(settings.auth_session_cookie_name)
    if token:
        await AuthStore(session).revoke_session(state_hash(token))
        await session.commit()
    response.delete_cookie(**cookie_kwargs())
    return no_store(response)
