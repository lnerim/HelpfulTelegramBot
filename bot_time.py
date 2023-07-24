# UTC
from dataclasses import dataclass
from datetime import datetime as dt

__DAY = 86400  # Время суток в секундах
__WEEK = 604800  # Время недели в секундах


@dataclass
class Time:
    start: float
    sleep: float
    end: float


def calculate_new_day() -> Time:
    time_now: float = dt.now().timestamp()
    t0: float = time_now % __DAY  # Время в секундах с начала суток
    time_start: float = time_now - t0  # Время в секундах начала суток

    return Time(
        start=time_start,
        sleep=time_start + __DAY - time_now,
        end=time_start + __DAY
    )


def calculate_new_week() -> Time:
    week_day = dt.now().weekday()  # Datetime: 0 - Понедельник, 6 - Воскресенье

    time_now: float = dt.now().timestamp()
    t0_day: float = time_now - time_now % __DAY  # Время в секундах начала суток
    time_start: float = t0_day - (__DAY * week_day)  # Время в секундах начала недели

    return Time(
        start=time_start,
        sleep=time_start + __WEEK - time_now,
        end=time_start + __WEEK
    )


def calculate_day_timer(hours: int, minutes: int) -> Time:
    time_start: float = calculate_new_day().start
    time_now: float = dt.now().timestamp()
    time_end: float = time_start + hours * 60 * 60 + minutes * 60

    if time_end < time_now:
        time_end += __DAY

    return Time(
        start=time_start,
        sleep=time_end - time_now,
        end=time_end
    )


if __name__ == "__main__":
    print("День: ", calculate_new_day())
    print("Неделя: ", calculate_new_week())
    print("Сегодня 12:24: ", calculate_day_timer(12, 24))
