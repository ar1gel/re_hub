import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from db.models import Base

logger = logging.getLogger(__name__)

_engine = None
_sessionmaker = None

_MIGRATIONS: list[str] = [
    "ALTER TABLE wb_accounts ADD COLUMN ignore_list TEXT DEFAULT ''",
]


async def _run_migrations() -> None:
    for sql in _MIGRATIONS:
        try:
            async with _engine.begin() as conn:
                await conn.execute(text(sql))
                logger.info("Migration applied: %s", sql[:60])
        except Exception:
            pass


async def init_db(database_url: str) -> None:
    global _engine, _sessionmaker
    _engine = create_async_engine(database_url, echo=False)
    _sessionmaker = async_sessionmaker(_engine, expire_on_commit=False)

    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await _run_migrations()


async def close_db() -> None:
    if _engine:
        await _engine.dispose()


def get_session() -> AsyncSession:
    return _sessionmaker()
