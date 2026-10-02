"""Explicit local retry of terminal jobs, without losing authenticated records."""
import argparse
import asyncio
from datetime import UTC, datetime
from uuid import UUID
from sqlalchemy import select, update


async def run(kind, job_id):
    from app.db.session import AsyncSessionLocal, dispose_db_engine
    from app.models import ReviewJob, WebhookJob
    model = WebhookJob if kind == "webhook" else ReviewJob
    try:
        async with AsyncSessionLocal() as session:
            if job_id is None:
                jobs = (await session.execute(select(model.id, model.status, model.retry_count).where(
                    model.status == "failed").order_by(model.created_at, model.id).limit(100))).all()
                for row in jobs:
                    print(f"{row.id} {row.status} attempts={row.retry_count}")
                return 0
            result = await session.execute(update(model).where(model.id == job_id, model.status == "failed").values(
                status="queued", retry_count=0, lease_until=None, lease_token=None,
                error_message=None, completed_at=None, available_at=datetime.now(UTC)))
            await session.commit()
            print("Failed job requeued." if result.rowcount else "No terminal failed job matched; completed and active jobs are unchanged.")
            return 0
    except Exception:
        print("Job retry unavailable; connection details are withheld.")
        return 1
    finally:
        await dispose_db_engine()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kind", choices=["webhook", "review"], required=True)
    parser.add_argument("--job-id", type=UUID, help="Without this option, list at most 100 failed job IDs.")
    args = parser.parse_args()
    from app.core.asyncio import configure_asyncio_event_loop_policy
    configure_asyncio_event_loop_policy()
    raise SystemExit(asyncio.run(run(args.kind, args.job_id)))
