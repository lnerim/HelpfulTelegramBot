from aiogram.filters.callback_data import CallbackData


class TaskData(CallbackData, prefix="rep"):
    num: int  # id задачи в БД
    user_id: int
    time: float
