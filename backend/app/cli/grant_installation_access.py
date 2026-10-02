"""Local administrator grants; never changes GitHub membership or App permissions."""
import argparse
import asyncio
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert


async def run(user_github_id, installation_github_id, revoke):
    from app.db.session import AsyncSessionLocal, dispose_db_engine
    from app.models import GitHubInstallation, User, UserInstallationAccess
    try:
        async with AsyncSessionLocal() as session:
            user = (await session.execute(select(User).where(User.github_user_id == user_github_id))).scalar_one_or_none()
            installation = (await session.execute(select(GitHubInstallation).where(GitHubInstallation.github_installation_id == installation_github_id))).scalar_one_or_none()
            if not user or not installation:
                print("User or synchronized installation not found.")
                return 1
            statement = insert(UserInstallationAccess).values(user_id=user.id, installation_id=installation.id, is_active=not revoke)
            await session.execute(statement.on_conflict_do_update(index_elements=[UserInstallationAccess.user_id, UserInstallationAccess.installation_id], set_={"is_active": not revoke}))
            await session.commit()
        print("Local installation access updated.")
        return 0
    except Exception:
        print("Local access update failed; connection details are withheld.")
        return 1
    finally:
        await dispose_db_engine()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--user-github-id", type=int, required=True)
    parser.add_argument("--installation-github-id", type=int, required=True)
    parser.add_argument("--revoke", action="store_true")
    args = parser.parse_args()
    from app.core.asyncio import configure_asyncio_event_loop_policy
    configure_asyncio_event_loop_policy()
    raise SystemExit(asyncio.run(run(args.user_github_id, args.installation_github_id, args.revoke)))
