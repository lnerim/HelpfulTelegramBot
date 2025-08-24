# Вроде плохо, конечно, что бот "одноразовый", но его развитие дальше и не пойдёт :(
import logging
import os

from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

from bot_database import Database

load_dotenv("bot.env")

# message_thread_id у тем в супергруппе
TOPIC_GENERAL = None
TOPIC_STAT = int(os.environ.get("TOPIC_STAT"))      # Статистика
TOPIC_REPORT = int(os.environ.get("TOPIC_REPORT"))  # Отчёты
TOPIC_CHAT = int(os.environ.get("TOPIC_CHAT"))      # Чат

SUPERGROUP_ID = int(os.environ.get("SUPERGROUP_ID"))

HASHTAG_TASK = ["workday", ]

TOKEN = os.environ["TOKEN"]
logging.basicConfig(
    level=logging.INFO,
    # filename='bot.log',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
bot = Bot(token=TOKEN)
dp = Dispatcher()
db = Database()
