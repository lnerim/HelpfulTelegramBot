from aiogram.filters.callback_data import CallbackData


class TaskData(CallbackData, prefix="rep"):
    num: int  # id задачи в БД
    user_id: int
    time: float


def convert_message(text: str, keys: tuple[str]) -> str:
    if not text.startswith(keys):
        raise SyntaxError("Некорректно использовано ключевое слово!")

    for stoke in keys:
        text = text.replace(stoke, "")

    c = 0
    while text and text[c] == " ":
        c += 1
    text = text[c:]  # Обрезаем первые пробелы после команды или хештега

    if text.isspace() or not text:
        raise ValueError("Отсутствует текст Вашего задания!")

    return text


def cut_list_dicts(arr: list, key: str, rate: int) -> (list, list):
    # Должно работать ТОЛЬКО при отсортированном списке
    n = len(arr)
    list1 = []
    for i in range(n):
        if arr[i][key] < rate:
            list2 = arr[i:]
            return list1, list2
        list1.append(arr[i])
