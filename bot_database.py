from datetime import datetime, timedelta, timezone

from sqlalchemy import Column, Integer, Float, String, DateTime, select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

Base = declarative_base()

# TODO Перенести бы в нормальное место
UTC_PLUS_3 = timezone(timedelta(hours=3))


class Record(Base):
    __tablename__ = "records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    value = Column(Float, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC_PLUS_3)
    )


class Database:
    def __init__(self, db_url="sqlite+aiosqlite:///data.db"):
        self.engine = create_async_engine(db_url, echo=False)
        self.async_session = async_sessionmaker(
            self.engine, expire_on_commit=False
        )

    async def init_db(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def add_record(self, user_id: int, value: float, description: str = None):
        async with self.async_session() as session:
            record = Record(user_id=user_id, value=value, description=description)
            session.add(record)
            await session.commit()

    async def get_records_by_day(self, days: int = 1):
        async with self.async_session() as session:
            since = datetime.now(UTC_PLUS_3) - timedelta(days=days)
            result = await session.execute(
                select(Record).where(Record.created_at >= since)
            )
            return result.scalars().all()

    async def get_all_records(self):
        async with self.async_session() as session:
            result = await session.execute(select(Record))
            return result.scalars().all()

    async def has_record_today(self, user_id: int) -> bool:
        async with self.async_session() as session:
            now = datetime.now(UTC_PLUS_3)  # текущее время в UTC+3
            start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)

            result = await session.execute(
                select(Record)
                .where(Record.user_id == user_id)
                .where(Record.created_at >= start_of_day)
            )
            return result.scalars().first() is not None
