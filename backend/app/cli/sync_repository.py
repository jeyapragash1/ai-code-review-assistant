import argparse
import asyncio

from app.clients.errors import GitHubError


async def run(owner: str | None, repo: str | None) -> int:
    # Delay configuration imports so misconfiguration cannot print validation inputs.
    try:
        from app.clients.github import GitHubClient
        from app.core.config import settings
        from app.db.session import AsyncSessionLocal, dispose_db_engine
        from app.schemas.github import RepositoryTarget
        from app.services.github.repository_sync import synchronize

        try:
            target = RepositoryTarget(
                owner=owner if owner is not None else settings.github_repository_owner,
                repo=repo if repo is not None else settings.github_repository_name,
            )
            async with GitHubClient(settings) as client, AsyncSessionLocal() as session:
                summary = await synchronize(client, session, target)
            print(summary.model_dump_json())
            return 0
        finally:
            await dispose_db_engine()
    except Exception as exc:
        # Only messages from our controlled error class may reach the terminal.
        print(str(exc) if isinstance(exc, GitHubError) else "Synchronization failed. Check local configuration and service availability.")
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Synchronize GitHub repository metadata and pull requests.")
    parser.add_argument("--owner")
    parser.add_argument("--repo")
    args = parser.parse_args()
    # Psycopg 3 requires SelectorEventLoop on Windows; configure before asyncio.run.
    from app.core.asyncio import configure_asyncio_event_loop_policy
    configure_asyncio_event_loop_policy()
    return asyncio.run(run(args.owner, args.repo))


if __name__ == "__main__":
    raise SystemExit(main())
