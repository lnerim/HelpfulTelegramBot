from typing import Union

from aiogram.filters import BaseFilter
from aiogram.types import Message


class HashtagFilter(BaseFilter):
    def __init__(self, hashtags: Union[str, list | tuple]):
        self.hashtags = hashtags

    async def __call__(self, message: Message) -> bool:
        if (text := message.text) is None:
            return False
        elif isinstance(self.hashtags, str):
            print(text.startswith("#" + self.hashtags))
            return text.startswith("#" + self.hashtags)
        else:
            for hashtag in self.hashtags:
                if text.startswith("#" + hashtag):
                    return True
            return False