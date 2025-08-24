import asyncio
from datetime import datetime, timedelta, timezone

UTC_PLUS_3 = timezone(timedelta(hours=3))

async def every_day_at(hour: int, minute: int, func):
    while True:
        now = datetime.now(UTC_PLUS_3)
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if next_run <= now:
            next_run += timedelta(days=1)  # если уже прошло время сегодня

        wait_seconds = (next_run - now).total_seconds()
        await asyncio.sleep(wait_seconds)
        try:
            await func()
        except Exception as e:
            print("Ошибка в daily task:", e)


async def every_week_at(weekday: int, hour: int, minute: int, func):
    while True:
        now = datetime.now(UTC_PLUS_3)
        # начало недели с понедельника 0, воскресенье 6
        days_ahead = (weekday - now.weekday()) % 7
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0) + timedelta(days=days_ahead)
        if next_run <= now:
            next_run += timedelta(weeks=1)

        wait_seconds = (next_run - now).total_seconds()
        await asyncio.sleep(wait_seconds)
        try:
            await func()
        except Exception as e:
            print("Ошибка в weekly task:", e)
