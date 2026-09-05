from collections.abc import AsyncIterator
from typing import Final

from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.asyncio import configure_asyncio_event_loop_policy
from app.core.config import settings

configure_asyncio_event_loop_policy()

POSTGRES_SCHEME: Final[str] = "postgresql"
ASYNC_POSTGRES_SCHEME: Final[str] = "postgresql+psycopg"


def _build_async_database_url(database_url: str) -> str:
    if not database_url:
        return database_url

    url = make_url(database_url)
    if url.drivername == POSTGRES_SCHEME:
        url = url.set(drivername=ASYNC_POSTGRES_SCHEME)
    if "schema" in url.query:
        url = url.difference_update_query(["schema"])

    return url.render_as_string(hide_password=False)


engine = create_async_engine(
    _build_async_database_url(settings.database_url),
    echo=False,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db_session() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        yield session


async def dispose_db_engine() -> None:
    await engine.dispose()
