from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()


@router.message(Command("info"))
async def filter_all_messages(message: Message):
    await message.answer(
        "Информация:\n"
        f"chat id = {message.chat.id}\n"
        f"chat type = {message.chat.type}\n"
        f"message_thread_id = {message.message_thread_id}"
    )
