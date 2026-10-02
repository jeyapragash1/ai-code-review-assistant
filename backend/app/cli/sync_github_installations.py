import argparse
import asyncio

from app.clients.errors import GitHubError


async def run() -> int:
    try:
        from app.core.config import settings
        from app.db.session import AsyncSessionLocal, dispose_db_engine
        from app.services.github.installation_sync import synchronize_installations

        try:
            async with AsyncSessionLocal() as session:
                summary = await synchronize_installations(settings, session)
            print(summary.model_dump_json())
            return 0
        finally:
            await dispose_db_engine()
    except Exception as exc:
        print(str(exc) if isinstance(exc, GitHubError) else "GitHub App synchronization failed. Check local configuration and service availability.")
        return 1


def main() -> int:
    argparse.ArgumentParser(description="Synchronize repositories accessible to GitHub App installations.").parse_args()
    from app.core.asyncio import configure_asyncio_event_loop_policy
    configure_asyncio_event_loop_policy()
    return asyncio.run(run())


if __name__ == "__main__":
    raise SystemExit(main())