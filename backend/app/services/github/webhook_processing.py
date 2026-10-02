from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert

from app.clients.github import GitHubClient
from app.clients.github_app import GitHubAppClient
from app.models import ActivityEvent, GitHubInstallation, InstallationRepositoryAccess, PullRequest, PullRequestStatus, Repository, WebhookEvent, WebhookEventStatus
from app.schemas.github import RepositoryTarget
from app.services.github.activity import event_timestamp, positive_id, safe_login, safe_metadata
from app.services.github.installation_sync import synchronize_installations
from app.services.github.repository_sync import synchronize
from app.services.jobs import queue_review


async def process_webhook(session, job, settings):
    event = await session.get(WebhookEvent, job.webhook_event_id)
    if event is None or event.status == WebhookEventStatus.IGNORED:
        raise ValueError("Authenticated webhook record unavailable.")
    payload = event.payload
    installation_payload = payload.get("installation")
    installation_github_id = positive_id(installation_payload.get("id")) if isinstance(installation_payload, dict) else None
    if installation_github_id is None:
        raise ValueError("Delivery has no valid installation.")
    installation = (await session.execute(select(GitHubInstallation).where(
        GitHubInstallation.github_installation_id == installation_github_id))).scalar_one_or_none()
    await session.commit()
    now = datetime.now(UTC)
    removed = event.event_name == "installation" and event.action in {"deleted", "suspend"}
    if removed:
        if installation:
            installation.is_active = False
            installation.suspended_at = now if event.action == "suspend" else installation.suspended_at
            await session.execute(update(InstallationRepositoryAccess).where(
                InstallationRepositoryAccess.installation_id == installation.id
            ).values(is_active=False, revoked_at=now))
            await session.commit()
    elif event.event_name in {"installation", "installation_repositories"} or installation is None:
        await synchronize_installations(settings, session)
        installation = (await session.execute(select(GitHubInstallation).where(
            GitHubInstallation.github_installation_id == installation_github_id))).scalar_one_or_none()
        await session.commit()
    repository = None
    if event.github_repository_id:
        repository = (await session.execute(select(Repository).where(
            Repository.github_repository_id == event.github_repository_id))).scalar_one_or_none()
        await session.commit()
        if installation and installation.is_active and not removed:
            async with GitHubAppClient(settings) as app_client:
                accessible = await app_client.installation_repositories(installation_github_id)
                target_repo = next((item for item in accessible if item.id == event.github_repository_id), None)
                if target_repo is None:
                    if repository:
                        await session.execute(update(InstallationRepositoryAccess).where(
                            InstallationRepositoryAccess.installation_id == installation.id,
                            InstallationRepositoryAccess.repository_id == repository.id
                        ).values(is_active=False, revoked_at=now))
                        await session.commit()
                else:
                    token = await app_client.installation_token(installation_github_id)
                    target = RepositoryTarget(owner=str(target_repo.owner.get("login", "")), repo=target_repo.name)
                    async with GitHubClient(settings, access_token=token.value) as client:
                        await synchronize(client, session, target)
                    repository = (await session.execute(select(Repository).where(
                        Repository.github_repository_id == event.github_repository_id))).scalar_one()
                    from app.repositories.github_installation import GitHubInstallationStore
                    await GitHubInstallationStore(session).upsert_access(installation.id, repository.id, now)
                    if event.event_name == "pull_request" and event.action in {"opened", "reopened", "synchronize"}:
                        pr = (await session.execute(select(PullRequest).where(PullRequest.repository_id == repository.id,
                            PullRequest.github_pr_number == event.github_pr_number))).scalar_one_or_none()
                        pr_payload = payload.get("pull_request", {})
                        head = pr_payload.get("head", {}) if isinstance(pr_payload, dict) else {}
                        if pr and pr.status == PullRequestStatus.OPEN and isinstance(head, dict) and head.get("sha") == pr.head_sha:
                            await queue_review(session, pr, trigger_type="webhook")
                    await session.commit()
    sender = payload.get("sender", {})
    sender = sender if isinstance(sender, dict) else {}
    await session.execute(insert(ActivityEvent).values(
        github_delivery_id=event.github_delivery_id, idempotency_key="delivery:" + event.github_delivery_id,
        installation_id=installation.id if installation else None,
        repository_id=repository.id if repository else None,
        actor_github_id=positive_id(sender.get("id")), actor_login=safe_login(sender.get("login")),
        event_type=event.event_name, event_action=event.action,
        safe_metadata=safe_metadata(event.event_name, payload),
        event_at=event_timestamp(payload, event.received_at), received_at=event.received_at,
        processing_status="completed", retry_count=job.retry_count,
    ).on_conflict_do_nothing(index_elements=[ActivityEvent.github_delivery_id]))
    event.status = WebhookEventStatus.COMPLETED
    event.attempt_count = job.retry_count
    event.processed_at = now
    event.error_message = None
    await session.commit()
