from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import CircleRecord


async def create_circle(session: AsyncSession, record: CircleRecord) -> CircleRecord:
    session.add(record)
    await session.commit()
    await session.refresh(record)
    return record


async def get_circle(session: AsyncSession, record_id: int) -> CircleRecord | None:
    return await session.get(CircleRecord, record_id)


async def list_circles(
    session: AsyncSession,
    user_id: int | None = None,
) -> list[CircleRecord]:
    query = select(CircleRecord).order_by(CircleRecord.data.desc())
    if user_id is not None:
        query = query.where(CircleRecord.user_id == user_id)
    result = await session.execute(query)
    return list(result.scalars())


async def delete_circle(session: AsyncSession, record: CircleRecord) -> None:
    await session.delete(record)
    await session.commit()
