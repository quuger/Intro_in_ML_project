from aiogram import Bot, Router, F, types
from aiogram.types import Message, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from filters import filters
import atexit
import utils.utils as utils
import os
import re

router = Router()


class DocumentStates(StatesGroup):
    waiting_for_name = State()


@router.message(Command("list"))
async def cmd_list(message: Message):
    if not utils.file_map:
        await message.answer("📭 Нет сохраненных файлов.")
        return
    
    response = "📋 Сохраненные файлы:\n\n"
    for i, (name, path) in enumerate(utils.file_map.items(), 1):
        file_size = os.path.getsize(path) if os.path.exists(path) else 0
        response += f"{i}. {name}\n"
        response += f"   📁 {os.path.basename(path)}\n"
        response += f"   📏 {file_size / 1024:.1f} KB\n\n"
    
    await message.answer(response)



@router.message(Command("delete"))
async def cmd_delete(message: Message):
    if not utils.file_map:
        await message.answer("📭 Нет файлов для удаления.")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    for name in utils.file_map.keys():
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text=f"❌ {name}", callback_data=f"delete_{name}")
        ])
    
    await message.answer("Выберите файл для удаления:", reply_markup=keyboard)


@router.callback_query(F.data.startswith("delete_"))
async def process_delete(callback):
    filename = callback.data.split("_", 1)[1]
    
    if filename in utils.file_map:
        file_path = utils.file_map[filename]
        
        if os.path.exists(file_path):
            os.remove(file_path)
        
        del utils.file_map[filename]
        
        await callback.message.answer(f"✅ Файл '{filename}' успешно удален.")
    else:
        await callback.message.answer("❌ Файл не найден.")
    
    await callback.answer()


@router.message(F.document)
async def handle_document(message: Message, state: FSMContext, bot: Bot):
    doc = message.document
    
    # Сохраняем временный файл
    temp_dir = "temp"
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, f"temp_{message.message_id}.json")
    
    try:
        # Скачиваем файл
        file = await bot.get_file(doc.file_id)
        await bot.download_file(file.file_path, temp_path)
        
        # Верифицируем JSON
        is_valid, error_msg = utils.verify_json_file(temp_path)
        
        if not is_valid:
            os.remove(temp_path)  # Удаляем временный файл
            await message.answer(f"❌ Ошибка валидации: {error_msg}")
            return
        
        # Сохраняем информацию о файле в состоянии
        await state.update_data(
            temp_file_path=temp_path,
            original_filename=doc.file_name or "document.json"
        )
        
        # Запрашиваем название у пользователя
        await message.answer(
            "✅ JSON файл прошел проверку!\n\n"
            "📝 Пожалуйста, введите название для этого файла "
            "(без расширения .json, оно добавится автоматически):\n\n"
            "Пример: 'настройки_бота' или 'user_data'"
        )
        
        # Переходим в состояние ожидания названия
        await state.set_state(DocumentStates.waiting_for_name)
        
    except Exception as e:
        await message.answer(f"❌ Ошибка при обработке файла: {str(e)}")
        if os.path.exists(temp_path):
            os.remove(temp_path)


@router.message(DocumentStates.waiting_for_name)
async def get_filename(message: Message, state: FSMContext):
    user_filename = message.text.strip()
    
    # Проверяем введенное название
    if not user_filename:
        await message.answer("❌ Название не может быть пустым. Попробуйте еще раз:")
        return
    
    if len(user_filename) > 100:
        await message.answer("❌ Название слишком длинное. Попробуйте еще раз:")
        return
    
    # Проверяем на недопустимые символы
    if re.search(r'[\\/*?!:"<>|]', user_filename):
        await message.answer(
            "❌ Название содержит недопустимые символы (\\/*?!:\"<>|). "
            "Попробуйте еще раз:"
        )
        return
    
    if user_filename in utils.file_map:
        await message.answer(
            f"❌ Файл с названием '{user_filename}' уже существует. "
            f"Пожалуйста, выберите другое название:"
        )
        return

    # Получаем данные из состояния
    data = await state.get_data()
    temp_path = data.get('temp_file_path')
    
    if not temp_path or not os.path.exists(temp_path):
        await message.answer("❌ Временный файл не найден. Отправьте файл заново.")
        await state.clear()
        return
    
    try:
        # Сохраняем файл в resources
        final_path = utils.save_file_to_resources(temp_path, user_filename)
        
        # Добавляем в мапу
        utils.file_map[user_filename] = final_path
        
        # Получаем информацию о файле
        file_size = os.path.getsize(temp_path)
        
        await message.answer(
            f"✅ Файл успешно сохранен!\n\n"
            f"📝 Название: {user_filename}\n"
            f"📁 Имя файла: {os.path.basename(final_path)}\n"
            f"📏 Размер: {file_size / 1024:.1f} KB\n"
            f"📂 Путь: {final_path}\n\n"
            f"Всего сохранено файлов: {len(utils.file_map)}"
        )
        
        # Удаляем временный файл
        os.remove(temp_path)
        
    except Exception as e:
        await message.answer(f"❌ Ошибка при сохранении файла: {str(e)}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
    
    # Очищаем состояние
    await state.clear()