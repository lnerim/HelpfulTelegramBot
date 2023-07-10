from dataclasses import dataclass
from datetime import datetime as dt


@dataclass
class Day:
    day_start: float
    sleep: float
    day_end: float


@dataclass
class Week:
    week_start: float
    sleep: float
    week_end: float


def calculate_new_day() -> Day:
    day = 86400  # Время суток в секундах

    time_now: float = dt.now().timestamp()
    t0: float = time_now % day  # Время в секундах с начала суток
    time_start: float = time_now - t0  # Время в секундах начала суток

    return Day(
        day_start=time_start,
        sleep=time_start + day - time_now,
        day_end=time_start + day
    )


def calculate_new_week():
    week_day = dt.now().weekday() + 1  # Datetime: 0 - Понедельник, 6 - Воскресенье
    day = 86400  # Время суток в секундах
    week = 604800  # Время недели в секундах

    time_now: float = dt.now().timestamp()
    t0: float = time_now % (day * week_day)  # Время в секундах с начала недели
    time_start: float = time_now - t0  # Время в секундах начала недели

    return Week(
        week_start=time_start,
        sleep=time_start + week - time_now,
        week_end=time_start + week
    )


if __name__ == "__main__":
    print(calculate_new_day())
    print(calculate_new_week())
