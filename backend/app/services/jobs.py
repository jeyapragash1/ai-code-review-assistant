"""Atomic queue claims, bounded retries and fenced completion for PostgreSQL."""
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import and_, or_, select, update
from sqlalchemy.dialects.postgresql import insert

from app.models import Review, ReviewJob, ReviewStatus
from app.repositories.review import ReviewStore


async def queue_review(session, pull_request, trigger_type="manual"):
    completed = await ReviewStore(session).completed_for_commit(pull_request.id, pull_request.head_sha)
    await session.execute(insert(ReviewJob).values(
        pull_request_id=pull_request.id, head_sha=pull_request.head_sha,
        trigger_type=trigger_type,
        status="completed" if completed else "queued",
        review_id=completed.id if completed else None,
        completed_at=datetime.now(UTC) if completed else None,
    ).on_conflict_do_nothing(index_elements=[ReviewJob.pull_request_id, ReviewJob.head_sha]))
    return (await session.execute(select(ReviewJob).where(
        ReviewJob.pull_request_id == pull_request.id, ReviewJob.head_sha == pull_request.head_sha
    ))).scalar_one()


async def claim_job(session, model, settings):
    now = datetime.now(UTC)
    # Crashed final attempts become terminal instead of remaining processing forever.
    await session.execute(update(model).where(model.status == "processing", model.lease_until <= now,
        model.retry_count >= settings.job_max_attempts).values(status="failed", lease_token=None,
        lease_until=None, error_message="Worker lease expired after the final attempt."))
    if model is ReviewJob:
        terminal_reviews = select(ReviewJob.review_id).where(ReviewJob.status == "failed",
            ReviewJob.retry_count >= settings.job_max_attempts, ReviewJob.review_id.is_not(None))
        await session.execute(update(Review).where(Review.id.in_(terminal_reviews),
            Review.status.notin_([ReviewStatus.COMPLETED, ReviewStatus.FAILED])).values(
                status=ReviewStatus.FAILED, error_code="worker_lease_expired",
                error_message="Worker lease expired after the final attempt.", completed_at=now))
    job = (await session.execute(select(model).where(
        model.retry_count < settings.job_max_attempts,
        or_(and_(model.status.in_(["queued", "retryable"]), model.available_at <= now),
            and_(model.status == "processing", model.lease_until <= now)),
    ).order_by(model.available_at, model.id).with_for_update(skip_locked=True).limit(1))).scalar_one_or_none()
    if job:
        job.status = "processing"
        job.retry_count += 1
        job.lease_token = uuid4()
        job.lease_until = now + timedelta(seconds=settings.job_lease_seconds)
        job.error_message = None
    await session.commit()
    return job


async def finish_job(session, model, job, settings, error=False, review_id=None):
    now = datetime.now(UTC)
    values = dict(status=("failed" if job.retry_count >= settings.job_max_attempts else "retryable") if error else "completed",
        lease_until=None, lease_token=None, error_message="Processing failed; check service configuration and permissions." if error else None,
        available_at=now + timedelta(seconds=min(300, 10 * 2 ** job.retry_count)),
        completed_at=None if error else now)
    if model is ReviewJob and review_id:
        values["review_id"] = review_id
    await session.execute(update(model).where(model.id == job.id, model.status == "processing",
        model.lease_token == job.lease_token).values(**values))
    await session.commit()
