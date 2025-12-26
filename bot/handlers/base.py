from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardRemove
from filters import filters
from config import config
import os
import re
import random

from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

from utils.models_manager import chatbot_model


router = Router()


@router.message(Command("help"))
async def cmd_help(message: Message):
    commands = [
        ("/start", "Начать работу"),
        ("/help", "Показать справку"),
        ("/list", "Список сохраненных файлов и моделей"),
        ("/delete", "Удалить файл или модель"),
        ("/switch", "Переключить модель"),
        ("/model_info", "Информация о текущей модели"),
    ]
    
    text = "🤖 <b>Доступные команды:</b>\n\n"
    for cmd, desc in commands:
        text += f"• <code>{cmd}</code> - {desc}\n"
    
    text += "\n📤 <b>Для загрузки файлов:</b>\n"
    text += "• <b>JSON файлы</b> - датасеты\n"
    text += "• <b>.pt файлы</b> - модели PyTorch\n\n"
    
    text += "💡 <b>Основные функции:</b>\n"
    text += "• Ответ на сообщения с упоминанием бота\n"
    text += "• Управление несколькими моделями\n"
    text += "• Сохранение и удаление датасетов и моделей\n"
    
    # Добавляем информацию о текущей модели, если она загружена
    current_model = chatbot_model.get_model_info()
    if current_model:
        text += f"\n✅ <b>Текущая модель:</b> <code>{current_model}</code>"
    
    await message.reply(text, parse_mode="HTML")


@router.message(filters.ReplyToBotFilter())
@router.message(filters.MentionFilter())
async def mention_handler(message: Message):
    print(f"GET_MSG: {message.text}")
    
    # Extract just the text without the mention if needed
    history = [message.text]

    if message.reply_to_message:
        history.append(message.reply_to_message.text)
        hisotry = reversed(history)
        print(history)

    # Generate response
    output = chatbot_model.generate_response(history)
    
    # Send response (truncate if too long for Telegram)
    if len(output) > 4000:
        output = output[:4000] + "..."
    
    if output:
        await message.reply(output)
    else:
        default_replies = ["Сори, это запретка", "Асуждаю", "Пожалуй, оставлю без ответа", "..."]
        await message.reply(random.choice(default_replies))