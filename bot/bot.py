import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command
from aiogram.fsm.storage.memory import MemoryStorage
from config import config
from handlers import base, other, resources
import atexit
from utils.utils import load_file_map, save_file_map

TOKEN = config.bot_token.get_secret_value()
atexit.register(save_file_map)


async def main():
    load_file_map()

    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.include_routers(base.router, other.router, resources.router)
    storage = MemoryStorage()

    await bot.delete_webhook(drop_pending_updates=True)
    try:
        await dp.start_polling(bot)
    finally:
        save_file_map()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())