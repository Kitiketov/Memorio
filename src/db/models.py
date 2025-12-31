from datetime import datetime

from sqlalchemy import BigInteger, DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class CircleRecord(Base):
    __tablename__ = "circle_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column("userid", BigInteger, index=True)
    data: Mapped[datetime] = mapped_column(
        "data",
        DateTime(timezone=True),
        server_default=func.now(),
    )
    location: Mapped[dict] = mapped_column("location", JSONB)
    type: Mapped[str] = mapped_column("type", String(32))
    media_id: Mapped[str] = mapped_column("mediaid", String(256))
    username: Mapped[str | None] = mapped_column("username", String(128), nullable=True)
    description: Mapped[str] = mapped_column("description", Text, default="")
