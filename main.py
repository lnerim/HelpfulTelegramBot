import asyncio
import logging

from config import db, dp, bot
from routers import router_main, router_stat, router_report
from timers import every_day_at, timer_stat_day


async def main():
    await db.init_db()

    logging.info("Бот запущен!")

    dp.include_router(router_main)
    dp.include_router(router_stat)
    dp.include_router(router_report)

    async with asyncio.TaskGroup() as tg:
        tg.create_task(every_day_at(23, 59, timer_stat_day))
        tg.create_task(dp.start_polling(bot))

if __name__ == "__main__":
    asyncio.run(main())
