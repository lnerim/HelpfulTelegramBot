from asyncio import sleep

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from config import SUPERGROUP_ID, TOPIC_REPORT, HASHTAG_TASK, db
from hashtag_filter import HashtagFilter

router = Router()


@router.message(Command("help"), F.chat.id == SUPERGROUP_ID, F.message_thread_id == TOPIC_REPORT)
async def report_messages(message: Message):
    msg = await message.answer(
        "Синтаксис\n"
        "#workday\n"
        "=\n"
        "- Невыполненная задача\n"
        "+ Выполненная задача\n"
        "%10/500 Процентная задача\n"
        "=\n"
        "Описание(опционально)\n"
        "\n"
        "Обязателен знак равно после хештега, второй не обязателен.\n"
        "Задач может не быть вовсе, количество ограничено лишь знаками в сообщении\n"
        "\n"
        "\n"
    )
    await message.delete()
    await sleep(30)
    await msg.delete()


@router.message(HashtagFilter(HASHTAG_TASK), F.chat.id == SUPERGROUP_ID, F.message_thread_id == TOPIC_REPORT)
async def report_messages(message: Message):
    elements: list[str] = message.text.split("=")

    # Описание даже не используется, может его и вообще игнорировать
    match elements:
        case [_, tasks_text]:
            desc = None
        case [_, tasks_text, desc]:
            if not desc.strip():  # is empty
                desc = None
            else:
                desc = desc.strip("\n")
        case _:
            await message.answer("неправильное количество элементов")
            return
    tasks_text: str = tasks_text.strip("\n")

    # Чтобы пустая строка не попала в список задач
    if not tasks_text.strip():
        tasks: list[str] = []
    else:
        tasks: list[str] = tasks_text.split("\n")

    normalize_task = []
    for task in tasks:
        if len(task) < 1:
            await message.answer(f"Неправильный синтаксис в задаче >{task}<")
            return

        task_op, *task_desc = task.split(" ", 1)

        if len(task_desc) == 0:
            await message.answer(f"Нет описания задачи >{task}<")
            return
        elif len(task_desc) == 1 and not task_desc[0].strip():
            await message.answer(f"Пустое описание задачи >{task}<")
            return

        task_desc = task_desc[0].strip()

        match task_op:
            case "-":
                percent = 0.0
            case "+":
                percent = 1.0
            case o if o.startswith("%"):
                nums = task_op[1:].split("/")
                if len(nums) != 2:
                    await message.answer(f"Неправильное количество чисел >{task}<")
                    return
                # Вроде на float тоже работает, не проверял, пусть так
                elif not ((first := nums[0]).isdigit() and (second := nums[1]).isdigit()):
                    await message.answer(f"Числа не распознаны >{task}<")
                    return
                percent = int(first) / int(second)
            case _:
                await message.answer(f"Нет такого оператора >{task_op}<")
                return

        new_task = (percent, task_desc)
        normalize_task.append(new_task)

    # TODO Проверить везде деление на ноль
    if len(normalize_task) == 0:
        return

    for t in normalize_task:
        await db.add_record(message.from_user.id, t[0], t[1])

    msg = await message.reply(f"Общий процент за день {sum(map(lambda x: x[0], normalize_task)) / len(normalize_task) * 100:.2f}%")
    await sleep(3)
    await msg.delete()


# @router.message(F.chat.id == SUPERGROUP_ID, F.message_thread_id == TOPIC_REPORT)
# async def report_messages(message: Message):
#     msg = await message.reply("Сообщение не обработано")
#     await sleep(3)
#     await message.delete()
#     await msg.delete()
