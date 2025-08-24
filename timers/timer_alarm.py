from config import bot, SUPERGROUP_ID, TOPIC_REPORT


async def timer_alarm():
    await bot.send_message(SUPERGROUP_ID, "Поделись своими итогами за день :) /help", message_thread_id=TOPIC_REPORT)