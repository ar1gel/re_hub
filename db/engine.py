from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from db.models import Base


_engine = None
_sessionmaker = None


async def init_db(database_url: str) -> None:
    global _engine, _sessionmaker
    _engine = create_async_engine(database_url, echo=False)
    _sessionmaker = async_sessionmaker(_engine, expire_on_commit=False)

    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    if _engine:
        await _engine.dispose()


def get_session() -> AsyncSession:
    return _sessionmaker()
