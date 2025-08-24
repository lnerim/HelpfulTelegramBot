from collections import defaultdict

from bot_database import Record
from config import db, bot, SUPERGROUP_ID, TOPIC_STAT


async def timer_stat_day():
    records: list[Record] = await db.get_records_by_day(1)

    results_day = defaultdict(lambda: {'count': 0, 'sum': 0.0})
    for record in records:
        results_day[record.user_id]['count'] += 1
        results_day[record.user_id]['sum'] += record.value

    top = []
    for key, value in results_day.items():
        member = await bot.get_chat_member(chat_id=SUPERGROUP_ID, user_id=key)
        username = member.user.full_name
        percent = value["sum"] / value["count"]
        top.append(
            ["🎖️", username, percent]
        )

    top.sort(key=lambda x: x[2])
    n = len(top)
    if n >= 1:
        top[0][0] = "🥇"
    if n >= 2:
        top[1][0] = "🥈"
    if n >= 3:
        top[2][0] = "🥉"


    text = "Статистика за день:\n\n"
    for emoji, username, percent in top:
        text += f"{emoji} {username} {percent*100:.2f}%\n"

    await bot.send_message(
        chat_id=SUPERGROUP_ID,
        text=text,
        message_thread_id=TOPIC_STAT
    )
