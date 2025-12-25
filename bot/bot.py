import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command
from aiogram.fsm.storage.memory import MemoryStorage
from config import config
from handlers import base, resources
import atexit
from utils.utils import load_all_maps, save_all_maps
from utils.models_manager import chatbot_model

TOKEN = config.bot_token.get_secret_value()
atexit.register(save_all_maps)


async def main():
    load_all_maps()

    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.include_routers(base.router, resources.router)
    storage = MemoryStorage()
    chatbot_model.load_model()

    await bot.delete_webhook(drop_pending_updates=True)
    try:
        await dp.start_polling(bot)
    finally:
        save_all_maps()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())