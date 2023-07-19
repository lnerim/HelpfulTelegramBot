import asyncio
import logging
import os
from time import time

from aiogram import Bot, Dispatcher, F
from aiogram.enums.chat_type import ChatType
from aiogram.types import ChatMemberMember, ChatMember, ContentType, CallbackQuery
from aiogram.types import Message, ChatMemberUpdated, User
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command

from bot_db import BotDataBase
from bot_time import *
from bot_utils import TaskData
from bot_filters import ChatTypeFilter, HashtagFilter


TOKEN = os.environ["TOKEN"]
logging.basicConfig(
    level=logging.INFO,
    # filename='bot.log',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
bot = Bot(token=TOKEN)
dp = Dispatcher()
db = BotDataBase()


@dp.message(Command(commands="start"), ChatTypeFilter(ChatType.PRIVATE))
async def cmd_start_private(message: Message):
    await message.answer(
        "Здравствуйте! Чтобы начать пользоваться ботом, его следует добавить в группу.\n/help"
    )


@dp.message(Command(commands="start"), ChatTypeFilter([ChatType.GROUP, ChatType.SUPERGROUP]))
async def cmd_start_private(message: Message):
    await bot.send_message(message.chat.id, "Я в группе! Введите /help")


@dp.message(Command(commands="help"), ChatTypeFilter([ChatType.PRIVATE, ChatType.GROUP, ChatType.SUPERGROUP]))
async def cmd_help(message: Message):
    await message.answer("Этот бот - групповой помощник для отслеживания Ваших полезных дел в группе Telegram. "
                         "Чтобы начать использовать бота, необходимо добавить его в группу Telegram. "
                         "После этого дать ему необходимые разрешения, а именно: чтение всех сообщений, "
                         "удаление сообщений.\n"
                         "\n"
                         "🤖 Команды бота:\n"
                         "* /start - Начало работы с ботом\n"
                         "* /help - Информационное сообщение об использовании ботом\n"
                         "* /status - Узнать количество набранных баллов за день и неделю\n"
                         "* /new_task - Создание нового задания.\n"
                         "* /mydailywork - То же самое, что и /new_task\n"
                         "\n"
                         "#️⃣ Хештеги\n"
                         "Помимо команд, бот также воспринимаешь хештеги: `#mydailywork` и `#new_task`.\n"
                         "\n"
                         "Синтаксис:\n"
                         "#mydailywork Выполнил очень крутое задание.\n"
                         "/new_task Выполнил ещё одно крутое задание.\n"
                         "\n"
                         "Помимо этого к хештегам можно прикрепить одно изображение. "
                         "Для этого нужно выбрать одно изображение и к нему прикрепить подпись с использованием "
                         "одного из хештегов точно также, как и без изображения. "
                         "Все остальные прикреплённые медиа будут игнорироваться. "
                         "\n"
                         "В конце дня и недели будет приходить собирательная статистика набранных баллов за "
                         "соответствующий промежуток времени. Ваши друзья могут помочь набрать вам больше баллов, "
                         "если сочтут ваше задание более полезным.")


@dp.message(Command(commands=["new_task", "mydailywork"]), ChatTypeFilter([ChatType.GROUP, ChatType.SUPERGROUP]))
@dp.message(ChatTypeFilter([ChatType.GROUP, ChatType.SUPERGROUP]),
            F.content_type.in_([ContentType.TEXT, ContentType.PHOTO, ContentType.VIDEO]),
            HashtagFilter(["new_task", "mydailywork"]))
async def create_task(message: Message):
    logging.debug(message)
    # Сразу откидываем ботов
    if message.from_user.is_bot:
        return

    # Если есть вложения, то
    if message.content_type == ContentType.TEXT:
        text = message.text
    else:
        text = message.caption
        if text is None:
            return

    me: User = await bot.get_me()
    keys = (
        "/new_task",
        "/mydailywork",
        "#new_task",
        "#mydailywork",
        f"@{me.username}"  # Имя бота, чтобы обращаться в чате через /command@bot_name
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
    task = db.task_add(
        user_id=message.from_user.id,
        group_id=message.chat.id,
        description=text,
        time=time()
    )
    logging.debug(f"Создано задание от {message.from_user.id} в группе {message.chat.id}: {text}")

    task_data = TaskData(
        num=task[0],
        user_id=message.from_user.id,
        time=task[1]
    )

    # Проверка на имя пользователя, т.к. не у всех есть
    if message.from_user.username is not None:
        user = f"<a href=\"t.me/{message.from_user.username}\">{message.from_user.full_name}</a>"
    else:
        user = message.from_user.full_name

    answer_text = f"{user} выполнил задание!\n\n" \
                  f"{text}\n" \
                  f"#task"

    # Inline Кнопка
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Полезно!",
        callback_data=task_data.pack()
    )

    # Если во вложении фото, то отправляем его
    if message.photo:
        await message.answer_photo(
            photo=message.photo[0].file_id,
            caption=answer_text,
            parse_mode="HTML",
            reply_markup=builder.as_markup()
        )
    else:
        await message.answer(
            answer_text,
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_markup=builder.as_markup()
        )

    # Если другое вложение, то не удаляем
    # Также другие вложения остаются
    if message.content_type in (ContentType.TEXT, ContentType.PHOTO):
        result: bool = await message.delete()
        logging.warning(f"Сообщение {message.message_id} из чата {message.chat.id} не удалилось!") if result else None


@dp.message(Command(commands=["status"]), ChatTypeFilter([ChatType.GROUP, ChatType.SUPERGROUP]))
async def cmd_status(message: Message):
    db.user_remember(message.from_user.id, message.chat.id)

    day: Time = calculate_new_day()
    week: Time = calculate_new_week()

    value_day = db.value_by_time(message.from_user.id, message.chat.id, day.start, day.end)
    value_week = db.value_by_time(message.from_user.id, message.chat.id, week.start, week.end)

    await message.reply("Статистика полученных баллов:\n"
                        f"За день: {value_day}\n"
                        f"За неделю: {value_week}\n")


@dp.my_chat_member
async def chat_update(update: ChatMemberUpdated):
    if update.new_chat_member.status == ChatMemberMember.MEMBER:
        if not db.group_check(update.chat.id):
            db.group_add(update.chat.id)
            logging.info(f"Новый чат: {update.chat.id}")
        else:
            db.group_update(update.chat.id, status=True)
            logging.info(f"Чат {update.chat.id} был снова добавлен")

    elif update.new_chat_member.status in [ChatMemberMember.RESTRICTED, ChatMemberMember.KICKED,
                                           ChatMemberMember.BANNED, ChatMemberMember.LEFT]:
        db.group_update(update.chat.id, status=False)
        logging.info(f"Чат {update.chat.id} выгнал бота")
        logging.info(f"Статус: {update.new_chat_member.status}")


@dp.callback_query(TaskData.filter())
async def callback_rep(callback: CallbackQuery):
    data: TaskData = TaskData.unpack(callback.data)
    user_id = callback.from_user.id

    if callback.from_user.id == data.user_id:
        await callback.answer("Нельзя изменить свой рейтинг!")
        return

    exist_rep: bool = db.rep_check(data.num, user_id)
    if exist_rep:
        db.rep_delete(data.num, user_id)
        db.task_update(data.num, -1)
        await callback.answer("Вы удалили свой голос!")
    else:
        db.rep_add(data.num, user_id)
        db.task_update(data.num, +1)
        await callback.answer("Вы повысили рейтинг задания!")


async def start_bot():
    await dp.start_polling(bot)


async def every_time(calc_time, desc: str):
    while True:
        t: Time = calc_time()
        await asyncio.sleep(t.sleep)
        groups = db.groups_by_status(status=True)

        async with asyncio.TaskGroup() as tg:
            for group in groups:
                group_id = group[1]
                users = db.users_by_group(group_id)

                tg.create_task(group_sender(
                    users=users,
                    group_id=group_id,
                    t_start=t.start,
                    t_end=t.end,
                    desc=desc
                ))


async def group_sender(users, group_id, t_start, t_end, desc=None):
    logging.info(f"Группа {group_id} получает рассылку за {desc}")
    text = f"Список активностей за {desc}\n"
    data = []
    for user_id in users:
        value = db.value_by_time(
            user_id=user_id,
            group_id=group_id,
            time_start=t_start,
            time_end=t_end
        )
        member: ChatMember = await bot.get_chat_member(group_id, user_id)
        full_name = member.user.full_name

        data.append(
            (value, full_name)
        )

    data.sort(reverse=True)
    for elem in data:
        text += f" * {elem[1]} - {elem[0]} б.\n"
    await bot.send_message(group_id, text)


async def main():
    logging.info("Бот запущен!")
    async with asyncio.TaskGroup() as tg:
        tg.create_task(every_time(calculate_new_day, "день"))
        tg.create_task(every_time(calculate_new_week, "неделю"))
        tg.create_task(start_bot())


if __name__ == "__main__":
    asyncio.run(main())
