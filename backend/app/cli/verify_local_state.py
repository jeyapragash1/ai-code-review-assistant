"""Read-only local counts and PR #1 fingerprints. Never prints record contents."""
import asyncio
import hashlib
import json
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import func, inspect, select


async def snapshot():
    from app.db.session import AsyncSessionLocal, dispose_db_engine, engine
    from app.models import ActivityEvent, GitHubCommit, GitHubInstallation, GitHubIssue, InstallationRepositoryAccess, PullRequest, Repository, Review, ReviewFinding, ReviewJob, WebhookJob, User, UserInstallationAccess, UserRepositoryAccess
    result = {}
    stage = "table inspection"
    try:
        async with engine.connect() as connection:
            tables = await connection.run_sync(lambda c: set(inspect(c).get_table_names()))
        async with AsyncSessionLocal() as session:
            stage = "table counts"
            for model in (GitHubInstallation, InstallationRepositoryAccess, Repository, PullRequest, GitHubIssue, GitHubCommit, Review, ReviewFinding, ActivityEvent, WebhookJob, ReviewJob, User, UserInstallationAccess, UserRepositoryAccess):
                if model.__tablename__ in tables:
                    result[model.__tablename__] = await session.scalar(select(func.count()).select_from(model))
            for key, column in [("public", Repository.is_private.is_(False)), ("private", Repository.is_private.is_(True)), ("fork", Repository.is_fork.is_(True)), ("archived", Repository.is_archived.is_(True))]:
                stage = "visibility counts"
                result[key] = await session.scalar(select(func.count()).select_from(Repository).where(column))
            for model, column, key in [(PullRequest, PullRequest.status, "pull_requests_by_state"), (GitHubIssue, GitHubIssue.state, "issues_by_state")]:
                stage = "state counts"
                rows = (await session.execute(select(column, func.count()).group_by(column))).all()
                result[key] = {str(state): count for state, count in rows}
            prs = select(PullRequest.id).where(PullRequest.github_pr_number == 1)
            review_ids = select(Review.id).where(Review.pull_request_id.in_(prs))
            for model, condition, key in [(PullRequest, PullRequest.id.in_(prs), "pr1_fingerprint"),
                (Review, Review.id.in_(review_ids), "pr1_reviews_fingerprint"),
                (ReviewFinding, ReviewFinding.review_id.in_(review_ids), "pr1_findings_fingerprint")]:
                stage = "PR preservation fingerprints"
                rows = (await session.execute(select(model.__table__).where(condition).order_by(model.id))).mappings().all()
                result[key] = hashlib.sha256(json.dumps([dict(row) for row in rows], sort_keys=True, default=str).encode()).hexdigest()
            if "user_repository_access" in tables:
                stage = "scoped dashboard queries"
                from app.api.v1.endpoints.account_dashboard import account_statistics
                from app.api.v1.scoped_session import ScopedReadSession
                from app.schemas.auth import AuthenticatedUser
                users = (await session.execute(select(User))).scalars().all()
                result["account_dashboard_counts"] = []
                for user in users:
                    identity = AuthenticatedUser(id=user.id, github_user_id=user.github_user_id, github_login=user.github_login,
                        display_name=None, email=None, avatar_url=None, profile_url=None, session_expires_at=datetime.now(UTC))
                    dashboard = await account_statistics(ScopedReadSession(session, identity), identity, None, None, None)
                    result["account_dashboard_counts"].append(dashboard.counts)
                # A synthetic in-memory identity has no grants and must see zero
                # real records. This never inserts a user or creates activity.
                unknown = AuthenticatedUser(id=uuid4(), github_user_id=2**62, github_login="ungranted-local-check",
                    display_name=None, email=None, avatar_url=None, profile_url=None, session_expires_at=datetime.now(UTC))
                isolated = await account_statistics(ScopedReadSession(session, unknown), unknown, None, None, None)
                result["ungranted_account_isolated"] = not any(isolated.counts.values())
                if not result["ungranted_account_isolated"]:
                    raise ValueError("Account isolation verification failed")
        stage = "advisory locking"
        lock_id = uuid4().int % (2**63 - 1)
        async with engine.connect() as first, engine.connect() as second:
            await first.execute(select(func.pg_advisory_lock(lock_id)))
            acquired = (await second.execute(select(func.pg_try_advisory_lock(lock_id)))).scalar_one()
            result["advisory_lock_isolation"] = acquired is False
            if acquired:
                await second.execute(select(func.pg_advisory_unlock(lock_id)))
            await first.execute(select(func.pg_advisory_unlock(lock_id)))
            await first.commit()
            await second.commit()
        print(json.dumps(result, sort_keys=True))
        return 0
    except Exception as exc:
        print(f"Local database verification unavailable at {stage} ({type(exc).__name__}); no connection details displayed.")
        return 1
    finally:
        await dispose_db_engine()


if __name__ == "__main__":
    from app.core.asyncio import configure_asyncio_event_loop_policy
    configure_asyncio_event_loop_policy()
    raise SystemExit(asyncio.run(snapshot()))
