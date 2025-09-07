from html import escape
from typing import List, Tuple

from aiogram.types import Message

from config import bot, SUPERGROUP_ID, TOPIC_STAT


def _truncate(text: str, limit: int) -> str:
    text = text.strip().replace("\n", " ")
    return text if len(text) <= limit else text[:limit].rstrip() + "…"


def _parse_report(message_text: str) -> tuple[list[tuple[str, float, str]], str | None]:
    parts = message_text.split("=")
    if len(parts) < 2:
        return [], None

    tasks_block = parts[1].strip("\n")
    desc_block = None
    if len(parts) >= 3 and parts[2].strip():
        desc_block = parts[2].strip()

    if not tasks_block.strip():
        return [], desc_block

    lines = [ln for ln in tasks_block.split("\n") if ln.strip()]
    tasks: list[tuple[str, float, str]] = []

    for ln in lines:
        op, *rest = ln.split(" ", 1)
        if not rest or not rest[0].strip():
            continue
        task_desc = rest[0].strip()

        if op == "+":
            cat, p = "done", 1.0
        elif op == "-":
            cat, p = "todo", 0.0
        elif op.startswith("%"):
            body = op[1:]  # всё после первого %
            if "/" in body:  # формат %3/5
                nums = body.split("/")
                try:
                    p = float(int(nums[0])) / float(int(nums[1]))
                    cat = "progress"
                except Exception:
                    continue  # некорректный формат — пропускаем
            elif body.endswith("%"):  # формат %41%
                num = body[:-1]
                if not num.isdigit():
                    continue
                p = int(num) / 100.0
                cat = "progress"
            else:
                continue
        else:
            continue

        tasks.append((cat, p, task_desc))

    return tasks, desc_block


def _build_compact_text(
    author_name: str,
    tasks: list[tuple[str, float, str]],
    desc_block: str | None,
    per_section_limit: int = 5,
) -> str:
    total = len(tasks)
    if total == 0:
        return f"<b>Отчёт от {escape(author_name)}</b>\n\nНет распознанных задач."

    done = [(c, p, d) for (c, p, d) in tasks if c == "done"]
    todo = [(c, p, d) for (c, p, d) in tasks if c == "todo"]
    prog = [(c, p, d) for (c, p, d) in tasks if c == "progress"]

    avg = sum(p for (_, p, _) in tasks) / total

    def pack_list(items: List[Tuple[str, float, str]], show_percent: bool = False) -> str:
        if not items:
            return "—"
        lines = []
        limit = min(len(items), per_section_limit)
        for i in range(limit):
            _, p, d = items[i]
            item = f"• {_truncate(escape(d), 80)}"
            if show_percent:
                item += f" ({int(round(p*100))}%)"
            lines.append(item)
        if len(items) > limit:
            lines.append(f"… и ещё {len(items) - limit}")
        return "\n".join(lines)

    text = []
    text.append(f"<b>Отчёт от {escape(author_name)}</b>")
    text.append("")
    text.append(f"Итог: <b>{avg*100:.2f}%</b> • задач: {total} "
                f"(выполнено: {len(done)}, в процессе: {len(prog)}, не выполнено: {len(todo)})")
    text.append("")
    if done:
        text.append("<u>Выполнено</u>")
        text.append(pack_list(done))
        text.append("")
    if prog:
        text.append("<u>В процессе</u>")
        text.append(pack_list(prog, show_percent=True))
        text.append("")
    if todo:
        text.append("<u>Не выполнено</u>")
        text.append(pack_list(todo))
        text.append("")

    if desc_block:
        short_desc = _truncate(escape(desc_block), 180)
        text.append("<b>Описание</b>")
        text.append(f"<blockquote>{short_desc}</blockquote>")

    return "\n".join(text).strip()


async def send_stat_now(message: Message) -> None:
    tasks, desc = _parse_report(message.text or "")
    author_name = message.from_user.full_name

    text = _build_compact_text(author_name=author_name, tasks=tasks, desc_block=desc)

    await bot.send_message(
        chat_id=SUPERGROUP_ID,
        text=text,
        message_thread_id=TOPIC_STAT,
        reply_to_message_id=message.message_id,
        parse_mode="HTML",
        disable_web_page_preview=True,
    )

