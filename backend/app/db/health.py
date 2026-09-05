import logging

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def check_database_connection(session: AsyncSession) -> bool:
    try:
        await session.execute(text("SELECT 1"))
    except SQLAlchemyError:
        logger.warning("Database connection check failed.")
        return False

    return True
