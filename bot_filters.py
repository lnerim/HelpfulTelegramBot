from typing import Union

from aiogram.enums import ContentType
from aiogram.filters import BaseFilter
from aiogram.types import Message


class ChatTypeFilter(BaseFilter):
    def __init__(self, chat_type: Union[str, list]):
        self.chat_type = chat_type

    async def __call__(self, message: Message) -> bool:
        if isinstance(self.chat_type, str):
            return message.chat.type == self.chat_type
        else:
            return message.chat.type in self.chat_type


class HashtagFilter(BaseFilter):
    def __init__(self, hashtags: Union[str, list]):
        self.hashtags = hashtags

    async def __call__(self, message: Message) -> bool:
        if message.content_type == ContentType.TEXT:
            text = message.text
        else:
            text = message.caption

        if isinstance(self.hashtags, str):
            return "#" + self.hashtags in text
        else:
            for hashtag in self.hashtags:
                if "#" + hashtag in text:
                    return True
            return False
