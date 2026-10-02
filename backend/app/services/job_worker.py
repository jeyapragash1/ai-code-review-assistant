import argparse
import asyncio
from types import SimpleNamespace

from sqlalchemy import func, select, update

from app.clients.github import GitHubClient
from app.clients.github_app import GitHubAppClient
from app.core.config import settings
from app.db.session import AsyncSessionLocal, dispose_db_engine, engine
from app.models import GitHubInstallation, InstallationRepositoryAccess, PullRequest, PullRequestStatus, Review, ReviewJob, ReviewStatus, ReviewTriggerType, WebhookJob
from app.services.jobs import claim_job, finish_job
from app.services.github.webhook_processing import process_webhook
from app.services.static_analysis.review_runner import run_static_review


async def process_review(session, job):
    if job.review_id:
        # Only the review linked to this reclaimed job can be marked failed.
        # The outer advisory lock proves the previous worker is no longer alive.
        await session.execute(update(Review).where(Review.id == job.review_id,
            Review.status.notin_([ReviewStatus.COMPLETED, ReviewStatus.FAILED])).values(
                status=ReviewStatus.FAILED, error_code="stale_worker", error_message="Previous worker lease expired."))
        await session.commit()
    pr = await session.get(PullRequest, job.pull_request_id)
    if pr is None or pr.status != PullRequestStatus.OPEN or pr.head_sha != job.head_sha:
        raise ValueError("Pull Request is closed or the queued commit is obsolete.")
    installation = (await session.execute(select(GitHubInstallation).join(InstallationRepositoryAccess).where(
        InstallationRepositoryAccess.repository_id == pr.repository_id,
        InstallationRepositoryAccess.is_active.is_(True), GitHubInstallation.is_active.is_(True),
        GitHubInstallation.suspended_at.is_(None)
    ).order_by(GitHubInstallation.id).limit(1))).scalar_one_or_none()
    await session.commit()
    if installation is None:
        raise ValueError("Repository installation access is unavailable.")
    async with GitHubAppClient(settings) as app_client:
        token = await app_client.installation_token(installation.github_installation_id)
        async with GitHubClient(settings, access_token=token.value) as client:
            return await run_static_review(client=client, session=session, settings=settings,
                pull_request_id=pr.id, expected_head_sha=job.head_sha, trigger_type=ReviewTriggerType(job.trigger_type),
                job_id=job.id, lease_token=job.lease_token)


async def run_once(model):
    async with AsyncSessionLocal() as session:
        job = await claim_job(session, model, settings)
        if job is None:
            return False
        # Rollbacks expire ORM attributes. Keep lease identity and routing
        # immutable so failure handling never performs implicit async I/O.
        job = SimpleNamespace(**{column.name: getattr(job, column.name) for column in model.__table__.columns})
        # A session advisory lock survives transaction commits. A stale lease
        # cannot start a second processor while the original worker is alive.
        lock_id = (job.pull_request_id if model is ReviewJob else job.id).int % (2**63 - 1)
        async with engine.connect() as lock_connection:
            locked = (await lock_connection.execute(select(func.pg_try_advisory_lock(lock_id)))).scalar_one()
            if not locked:
                await finish_job(session, model, job, settings, error=True)
                return True
            try:
                async with asyncio.timeout(settings.job_timeout_seconds):
                    summary = await process_review(session, job) if model is ReviewJob else await process_webhook(session, job, settings)
                await finish_job(session, model, job, settings, review_id=summary.review_id if model is ReviewJob else None)
            except Exception:
                await session.rollback()
                await finish_job(session, model, job, settings, error=True)
            finally:
                await lock_connection.execute(select(func.pg_advisory_unlock(lock_id)))
                await lock_connection.commit()
        return True


async def run(model, once):
    try:
        while True:
            processed = await run_once(model)
            if once:
                return 0
            if not processed:
                await asyncio.sleep(2)
    finally:
        await dispose_db_engine()


def main(model):
    parser = argparse.ArgumentParser(description="Process durable database jobs with bounded retries.")
    parser.add_argument("--once", action="store_true", help="Process at most one eligible job and exit.")
    args = parser.parse_args()
    try:
        return asyncio.run(run(model, args.once))
    except KeyboardInterrupt:
        return 0
    except Exception:
        print("Worker unavailable; check database and configuration.")
        return 1
