from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.engine.url import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config import settings
from src.db.models import Base


engine = create_async_engine(settings.database_url, echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def ensure_database_exists() -> None:
    url = make_url(settings.database_url)
    database = url.database
    if not database:
        return

    maintenance_url = url.set(database="postgres")
    maintenance_engine = create_async_engine(
        maintenance_url,
        echo=False,
        isolation_level="AUTOCOMMIT",
    )
    try:
        async with maintenance_engine.connect() as conn:
            result = await conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": database},
            )
            if result.scalar() is None:
                safe_database = database.replace('"', '""')
                await conn.execute(text(f'CREATE DATABASE "{safe_database}"'))
    finally:
        await maintenance_engine.dispose()


async def start_db() -> None:
    await ensure_database_exists()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(
            text(
                "ALTER TABLE circle_records "
                "ADD COLUMN IF NOT EXISTS username VARCHAR(128)"
            )
        )


async def stop_db() -> None:
    await engine.dispose()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session
