from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardRemove
from filters import filters

router = Router()

# Хэндлер на команду /start
@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет!")

@router.message(Command("test1"))
async def cmd_test1(message: types.Message):
    await message.reply("Test 1")

@router.message(Command("dice"))
async def cmd_dice(message: types.Message):
    await message.answer_dice(emoji="🎲")

@router.message(Command("special_buttons"))
async def cmd_start(message: types.Message):
    kb = [
        [
            types.KeyboardButton(text="С пюрешкой"),
            types.KeyboardButton(text="Без пюрешки")
        ],
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Выберите способ подачи",
        one_time_keyboard=True,
        selective=True,
    )
    await message.reply("Как подавать котлеты?", reply_markup=keyboard)

@router.message(F.text.lower() == "с пюрешкой")
async def with_puree(message: types.Message):
    await message.reply("Отличный выбор!")

@router.message(F.text.lower() == "без пюрешки")
async def without_puree(message: types.Message):
    await message.reply("Так невкусно!")


@router.message(filters.MentionFilter())
async def mention_handler(message: Message):
    await message.reply("Привет! Я увидел, что вы меня упомянули!")