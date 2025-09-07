import logging
from asyncio import sleep

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

from config import TOPIC_STAT, SUPERGROUP_ID
from timers.timer_stat_day import timer_stat_day

router = Router()


@router.message(F.chat.id == SUPERGROUP_ID, F.message_thread_id == TOPIC_STAT)
async def stat_messages(message: Message):
    if message.from_user.is_bot:
        logging.warning(f"Пользователь это бот user_id={message.from_user.id}")
        return

    await message.delete()
    msg = await message.bot.send_message(message.chat.id, "Тут нельзя писать, только статистика", message_thread_id=TOPIC_STAT)
    await sleep(3)
    await msg.delete()

@router.message(Command("testday"))
async def testday(message: Message):
    await timer_stat_day()


