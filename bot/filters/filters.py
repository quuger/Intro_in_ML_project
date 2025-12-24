from aiogram import Bot
from aiogram.types import Message
from aiogram.filters import BaseFilter
import asyncio


class MentionFilter(BaseFilter):
    async def __call__(self, message: Message, bot: Bot) -> bool:
        bot_info = await bot.get_me()
        bot_username = bot_info.username
        return (message.text and 
                bot_username and 
                f"@{bot_username}" in message.text)