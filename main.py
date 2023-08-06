import asyncio
import logging
import os
from time import time

from aiogram import Bot, Dispatcher, F
from aiogram.enums.chat_type import ChatType
from aiogram.types import ChatMemberMember, ContentType, CallbackQuery, BotCommand
from aiogram.types import Message, ChatMemberUpdated, User
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton
from aiogram.filters import Command

from bot_db import BotDataBase
from bot_time import *
from bot_utils import TaskData, convert_message, cut_list_dicts, DeleteTaskData
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
            F.content_type.in_([ContentType.TEXT, ContentType.PHOTO, ContentType.VIDEO, ContentType.DOCUMENT]),
            HashtagFilter(["new_task", "mydailywork"]))
async def create_task(message: Message):
    logging.debug(message)
    # Сразу откидываем ботов
    if message.from_user.is_bot:
        return

    me: User = await bot.get_me()
    keys: tuple = (
        "/new_task",
        "/mydailywork",
        "#new_task",
        "#mydailywork",
        f"@{me.username}"  # Имя бота, чтобы обращаться в чате через /command@bot_name
    )

    try:
        text = convert_message(message.html_text, keys)

    except SyntaxError:
        await message.answer(
            "Некорректно использовано ключевое слово!\n"
            "Синтаксис:\n"
            "<u>#new_task Выполненное задание</u>\n"
            "/help - примеры использования",
            parse_mode="HTML"
        )
        return

    except ValueError:
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

    user = f"<a href='tg://user?id={message.from_user.id}'>{message.from_user.full_name}</a>"

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
        logging.warning(f"Сообщение {message.message_id} из чата {message.chat.id} не удалено!") if not result else ...


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


@dp.message(Command(commands="delete"), ChatTypeFilter([ChatType.GROUP, ChatType.SUPERGROUP]))
async def cmd_delete(message: Message):
    day: Time = calculate_new_day()
    # num, user_id, group_id, desc, value, time
    tasks: list[tuple | None] = db.tasks_by_time(message.from_user.id, message.chat.id, day.start, day.end)

    if not tasks:
        await message.answer("Увы, но у Вас нет выполненных заданий за день!")
        return

    builder = InlineKeyboardBuilder()
    for task in tasks:
        del_task_data = DeleteTaskData(
            num=task[0],
            user_id=task[1]
        )
        btn = InlineKeyboardButton(
            text=task[3],
            callback_data=del_task_data.pack()
        )
        builder.row(btn)

    new_message = await message.answer(
        text="Нажмите на кнопку с заданием, чтобы удалить его",
        reply_markup=builder.as_markup()
    )

    await asyncio.sleep(5*60)
    await message.delete()
    await new_message.delete()


@dp.message(Command(commands="vacation_add"), ChatTypeFilter([ChatType.GROUP, ChatType.SUPERGROUP]))
async def cmd_vacation_add(message: Message):
    text: list[str] = message.text.split(" ")
    if len(text) != 2 or not text[1].isdigit() or (days := int(text[1])) <= 0:
        await message.answer("Некорректный синтаксис.\nНужно:\n"
                             "/vacation_add <дни отпуска>\n"
                             "Где дни следует указывать в целых числах")
        return

    result = db.vacation_add(message.from_user.id, message.chat.id, days)
    if result[0]:
        await message.answer(f"Отпуск спешно создан, наслаждайтесь бездельем {result[1]} дня(ей)!")
    else:
        await message.answer(f"У Вас уже активен отпуск, до окончания {result[1]} дня(ей)!")


@dp.message(Command(commands="vacation_status"), ChatTypeFilter([ChatType.GROUP, ChatType.SUPERGROUP]))
async def cmd_vacation_status(message: Message):
    if (status := db.vacation_status(message.from_user.id, message.chat.id)) is None:
        await message.answer("У Вас нет сейчас активного отпуска!")
    else:
        await message.answer(f"У Вас осталось {status} дня(ей) до конца отпуска!")


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

    if user_id == data.user_id:
        await callback.answer("Нельзя изменить свой рейтинг!")
        return

    if db.task_get(data.num) is None:
        await callback.answer("Не существует такого задания!")
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


@dp.callback_query(DeleteTaskData.filter())
async def callback_delete(callback: CallbackQuery):
    del_data: DeleteTaskData = DeleteTaskData.unpack(callback.data)

    if db.task_get(del_data.num) is None:
        await callback.answer("Не существует такого задания!")
        return

    db.task_delete(del_data.num)
    await callback.answer("Задание удалено!")


async def every_time(calc_time: callable, desc: str, rate: int):
    while True:
        t: Time = calc_time()
        await asyncio.sleep(t.sleep)
        groups = db.groups_by_status(status=True)

        async with asyncio.TaskGroup() as tg:
            for group in groups:
                group_id = group[1]
                users = db.users_by_group(group_id)

                tg.create_task(
                    group_sender(users, group_id, t.start, t.end, desc, rate)
                )


async def group_sender(users: tuple, group_id: int, t_start: float, t_end: float, desc: str, rate: int):
    logging.info(f"Группа {group_id} получает рассылку за {desc}")

    data = []
    for user_id in users:
        value = db.value_by_time(user_id, group_id, t_start, t_end)
        member: ChatMemberMember = await bot.get_chat_member(group_id, user_id)

        data.append(
            {
                "value": value,
                "name": member.user.full_name,
                "id": member.user.id
            }
        )

    if not data:
        return

    data = sorted(data, key=lambda x: x["value"], reverse=True)
    data_good, data_bad = cut_list_dicts(data, "value", rate)
    del data

    if data_good:
        top = -1  # Значение точно станет нулём при первой итерации
        remember = 0  # Число точно не встречается
        emoji = ["🥇", "🥈", "🥉", "🎖️"]
        text_good = f"Список активностей за {desc}\n"
        for elem in data_good:
            # Пример: 🥇 Иван - 10 б.
            if (top < len(emoji) - 1) and (remember != elem["value"]):
                top += 1
            text_good += f" {emoji[top]} <a href='tg://user?id={elem['id']}'>{elem['name']}</a> - {elem['value']} б.\n"
            remember = elem["value"]

        await bot.send_message(group_id, text_good, parse_mode="HTML")

    if data_bad:
        text_bad = f"А вот и бездельники за {desc}! Покайтесь и больше так не делайте!\n"
        lazybones = ", ".join(
            f"<a href='tg://user?id={elem['id']}'>{elem['name']}</a>" for elem in data_bad
        )

        await bot.send_message(group_id, text_bad + lazybones, parse_mode="HTML")


async def set_commands():
    await bot.set_my_commands(commands=[
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="help", description="Помощь по боту"),
        BotCommand(command="new_task", description="Выполнение задания"),
        BotCommand(command="status", description="Статус за день/неделю"),
        BotCommand(command="delete", description="Удаление заданий"),
        BotCommand(command="vacation_add", description="Создать отпуск"),
        BotCommand(command="vacation_status", description="Статус отпуска"),
    ])


async def main():
    logging.info("Бот запущен!")
    await set_commands()
    async with asyncio.TaskGroup() as tg:
        tg.create_task(every_time(calculate_new_day, "день", 1))
        tg.create_task(every_time(calculate_new_week, "неделю", 7))
        tg.create_task(dp.start_polling(bot))


if __name__ == "__main__":
    asyncio.run(main())
