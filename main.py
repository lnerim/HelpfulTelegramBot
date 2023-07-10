import os
import asyncio
import logging
from time import time
from aiogram import Bot, Dispatcher
from aiogram.types import Message, ChatType, ChatMemberUpdated, ChatMemberStatus, ChatMember
from bot_db import BotDataBase
from bot_time import *


TOKEN = os.environ["TOKEN"]
logging.basicConfig(
    level=logging.INFO,
    # filename='bot.log',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
db = BotDataBase()


@dp.message_handler(chat_type=ChatType.PRIVATE, commands="start")
async def cmd_start_private(message: Message):
    await message.answer(
        "Здравствуйте! Чтобы начать пользоваться ботом, его следует добавить в группу.\n/help"
    )


@dp.message_handler(chat_type=[ChatType.GROUP, ChatType.SUPERGROUP], commands="start")
async def cmd_start_private(message: Message):
    await bot.send_message(message.chat.id, "Я в группе!")


@dp.message_handler(commands=["help"])
async def cmd_help(message: Message):
    # TODO: добавить нормальное описание
    await message.answer("В разработке!")


@dp.message_handler(chat_type=[ChatType.GROUP, ChatType.SUPERGROUP], commands=["new_task", "mydailywork"])
@dp.message_handler(chat_type=[ChatType.GROUP, ChatType.SUPERGROUP], hashtags=["new_task", "mydailywork"])
async def create_task(message: Message):
    logging.info(message)
    if message.from_user.is_bot:
        return

    text = message.text
    keys = (
        "/new_task",
        "/mydailywork",
        "#new_task",
        "#mydailywork"
    )

    if not text.startswith(keys):
        await message.answer(
            "Некорректно использовано ключевое слово!\n"
            "Синтаксис:\n"
            "<u>#new_task Выполненное задание</u>\n"
            "/help - примеры использования",
            parse_mode="HTML"
        )
        return

    for stoke in keys:
        text = text.replace(stoke, "")
    text = text[1:]  # Обрезаем первый пробел после команды или хештега

    if text.isspace() or not text:
        await message.answer(
            "Отсутствует текст Вашего задания!\n"
            "Синтаксис:\n"
            "<u>#new_task Выполненное задание</u>\n"
            "/help - примеры использования",
            parse_mode="HTML"
        )
        return

    # Создание задания
    db.user_remember(
        user_id=message.from_user.id,
        group_id=message.chat.id
    )
    db.task_add(
        user_id=message.from_user.id,
        group_id=message.chat.id,
        description=text,
        time=time()
    )
    logging.info(f"Создано задание от {message.from_user.id} в группе {message.chat.id}: {text}")

    # Проверка на имя пользователя, т.к. не у всех есть
    if message.from_user.username is not None:
        user = f"<a href=\"t.me/{message.from_user.username}\">{message.from_user.full_name}</a>\n"
    else:
        user = message.from_user.full_name

    await message.answer(
        user + " выполнил задание!\n\n" +
        text + "\n" +
        "#task",
        parse_mode="HTML"
    )


@dp.my_chat_member_handler()
async def chat_update(update: ChatMemberUpdated):
    if update.new_chat_member.status == ChatMemberStatus.MEMBER:
        if not db.group_check(update.chat.id):
            db.group_add(update.chat.id)
            logging.info(f"Новый чат: {update.chat.id}")
        else:
            db.group_update(update.chat.id, status=True)
            logging.info(f"Чат {update.chat.id} был снова добавлен")

    elif update.new_chat_member.status in [ChatMemberStatus.RESTRICTED, ChatMemberStatus.KICKED,
                                           ChatMemberStatus.BANNED, ChatMemberStatus.LEFT]:
        db.group_update(update.chat.id, status=False)
        logging.info(f"Чат {update.chat.id} выгнал бота")
        logging.info(f"Статус: {update.new_chat_member.status}")


async def start_bot():
    await dp.start_polling(bot)


async def every_day():
    while True:
        day: Day = calculate_new_day()
        await asyncio.sleep(day.sleep)
        groups = db.groups_by_status(status=True)

        async with asyncio.TaskGroup() as tg:
            for group in groups:
                group_id = group[1]
                users = db.users_by_group(group_id)

                tg.create_task(group_sender(
                    users=users,
                    group_id=group_id,
                    t_start=day.day_start,
                    t_end=day.day_end,
                    desc="неделю"
                ))


async def every_week():
    while True:
        week: Week = calculate_new_week()
        await asyncio.sleep(week.sleep)
        groups = db.groups_by_status(status=True)

        async with asyncio.TaskGroup() as tg:
            for group in groups:
                group_id = group[1]
                users = db.users_by_group(group_id)

                tg.create_task(group_sender(
                    users=users,
                    group_id=group_id,
                    t_start=week.week_start,
                    t_end=week.week_end,
                    desc="неделю"
                ))


async def group_sender(users, group_id, t_start, t_end, desc=None):
    text = f"Список активностей за {desc}\n"
    for user_id in users:
        tasks = db.tasks_by_time(
            user_id=user_id,
            group_id=group_id,
            time_start=t_start,
            time_end=t_end
        )
        # value - 4 индекс
        sum_value = sum(i[4] for i in tasks)
        member: ChatMember = await bot.get_chat_member(group_id, user_id)
        full_name = member.user.full_name
        text += f" * {full_name} - {sum_value} б.\n"
    await bot.send_message(group_id, text)


async def main():
    async with asyncio.TaskGroup() as tg:
        tg.create_task(every_day())
        tg.create_task(every_week())
        tg.create_task(start_bot())


if __name__ == "__main__":
    asyncio.run(main())
