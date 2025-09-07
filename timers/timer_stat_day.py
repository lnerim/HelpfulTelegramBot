# timers/timer_stat_day.py
from collections import defaultdict
from html import escape

from bot_database import Record
from config import db, bot, SUPERGROUP_ID, TOPIC_STAT


async def timer_stat_day():
    # Берём записи за последние 24 часа
    records: list[Record] = await db.get_records_by_day(1)  # :contentReference[oaicite:0]{index=0}

    if not records:
        await bot.send_message(
            chat_id=SUPERGROUP_ID,
            text="<b>Статистика за день</b>\n\nЗаписей за сегодня нет.",
            message_thread_id=TOPIC_STAT,
            parse_mode="HTML",
            disable_web_page_preview=True,
        )
        return

    # Агрегация по пользователям:
    # total — всего задач; sum — сумма значений; по категориям: done/progress/todo
    agg = defaultdict(lambda: {"total": 0, "sum": 0.0, "done": 0, "progress": 0, "todo": 0})
    for r in records:
        st = agg[r.user_id]
        st["total"] += 1
        st["sum"] += float(r.value)

        # Классификация по типу задачи:
        # + -> 1.0 (выполнено), - -> 0.0 (не выполнено), % -> (0..1) (в процессе)
        if r.value >= 0.999999:
            st["done"] += 1
        elif r.value <= 0.000001:
            st["todo"] += 1
        else:
            st["progress"] += 1

    rows = []
    for user_id, st in agg.items():
        # Получаем отображаемое имя пользователя из чата статистики
        try:
            member = await bot.get_chat_member(chat_id=SUPERGROUP_ID, user_id=user_id)
            username = member.user.full_name or str(user_id)
        except Exception:
            username = str(user_id)

        total = st["total"]
        avg_percent = (st["sum"] / total) * 100 if total else 0.0  # общий процент по всем задачам

        rows.append({
            "username": username,
            "avg_percent": avg_percent,
            "done": st["done"],
            "progress": st["progress"],
            "todo": st["todo"],
        })

    # Сортируем для читабельности по общему проценту (по убыванию), затем по числу выполненных
    rows.sort(key=lambda x: (x["avg_percent"], x["done"]), reverse=True)

    # Формируем текст
    lines = [
        "<b>Статистика за день</b>",
        "<i>Выполненные задачи и их процент</i>",
        "",
    ]
    nb = " " * 4  # отступ для подпунктов
    for row in rows:
        lines.append(
            f"• <b>{escape(row['username'])}</b> (общий процент {row['avg_percent']:.2f}%):"
        )
        lines.append(f"{nb}— Выполнено: {row['done']}")
        lines.append(f"{nb}— В процессе: {row['progress']}")
        lines.append(f"{nb}— Не выполнено: {row['todo']}")
        lines.append("")  # пустая строка между пользователями

    text = "\n".join(lines).rstrip()

    await bot.send_message(
        chat_id=SUPERGROUP_ID,
        text=text,
        message_thread_id=TOPIC_STAT,
        parse_mode="HTML",
        disable_web_page_preview=True,
    )

