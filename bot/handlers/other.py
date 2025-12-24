from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()

@router.message(Command("help"))
async def cmd_help(message: Message):
    commands = [
        ("/start", "Начать работу"),
        ("/help", "Показать справку"),
        ("/list", "Список сохраненных файлов"),
        ("/delete", "Удалить файл"),
        ("/dice", "Бросить кубик"),
        ("/special_buttons", "Тестовая клавиатура"),
    ]
    
    text = "📚 <b>Доступные команды:</b>\n\n"
    for cmd, desc in commands:
        text += f"• <code>{cmd}</code> - {desc}\n"
    
    text += "\n📤 <b>Для загрузки:</b> просто отправьте JSON файл"
    
    await message.answer(text, parse_mode="HTML")