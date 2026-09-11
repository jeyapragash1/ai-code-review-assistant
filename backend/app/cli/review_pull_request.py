import argparse
import asyncio
from uuid import UUID

from app.clients.errors import GitHubError
from app.services.static_analysis.review_runner import StaticReviewError


def parse_repository(value: str) -> tuple[str, str]:
    parts = value.split("/")
    if len(parts) != 2 or not all(parts):
        raise argparse.ArgumentTypeError("Repository must be in owner/name form.")
    return parts[0], parts[1]


async def run(repository: str | None, pr_number: int | None, pull_request_id: UUID | None, force: bool) -> int:
    try:
        from app.clients.github import GitHubClient
        from app.core.config import settings
        from app.db.session import AsyncSessionLocal, dispose_db_engine
        from app.schemas.github import RepositoryTarget
        from app.services.static_analysis.review_runner import run_static_review

        if pull_request_id is None and (repository is None or pr_number is None):
            print("Provide --pull-request-id or both --repository and --pr-number.")
            return 1
        owner = repo = None
        if repository is not None:
            owner, repo = parse_repository(repository)
            RepositoryTarget(owner=owner, repo=repo)

        try:
            async with GitHubClient(settings) as client, AsyncSessionLocal() as session:
                summary = await run_static_review(
                    client=client,
                    session=session,
                    settings=settings,
                    pull_request_id=pull_request_id,
                    repository_full_name=f"{owner}/{repo}" if owner and repo else None,
                    pr_number=pr_number,
                    force=force,
                )
            print(summary.model_dump_json())
            return 0 if summary.final_status.value == "completed" else 1
        finally:
            await dispose_db_engine()
    except (GitHubError, StaticReviewError) as exc:
        print(str(exc))
        return 1
    except Exception:
        print("Static review failed. Check local configuration and service availability.")
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a local static-analysis review for a synchronized Pull Request.")
    parser.add_argument("--repository", help="Repository full name, for example owner/name.")
    parser.add_argument("--pr-number", type=int)
    parser.add_argument("--pull-request-id", type=UUID)
    parser.add_argument("--force", action="store_true", help="Create the next attempt even if this commit already has a completed review.")
    args = parser.parse_args()
    from app.core.asyncio import configure_asyncio_event_loop_policy
    configure_asyncio_event_loop_policy()
    return asyncio.run(run(args.repository, args.pr_number, args.pull_request_id, args.force))


if __name__ == "__main__":
    raise SystemExit(main())
