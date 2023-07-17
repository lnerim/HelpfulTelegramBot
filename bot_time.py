from dataclasses import dataclass
from datetime import datetime as dt


@dataclass
class Time:
    start: float
    sleep: float
    end: float


def calculate_new_day() -> Time:
    day = 86400  # Время суток в секундах

    time_now: float = dt.now().timestamp()
    t0: float = time_now % day  # Время в секундах с начала суток
    time_start: float = time_now - t0  # Время в секундах начала суток

    return Time(
        start=time_start,
        sleep=time_start + day - time_now,
        end=time_start + day
    )


def calculate_new_week() -> Time:
    week_day = dt.now().weekday() + 1  # Datetime: 0 - Понедельник, 6 - Воскресенье
    day = 86400  # Время суток в секундах
    week = 604800  # Время недели в секундах

    time_now: float = dt.now().timestamp()
    t0: float = time_now % (day * week_day)  # Время в секундах с начала недели
    time_start: float = time_now - t0  # Время в секундах начала недели

    return Time(
        start=time_start,
        sleep=time_start + week - time_now,
        end=time_start + week
    )


if __name__ == "__main__":
    print(calculate_new_day())
    print(calculate_new_week())
