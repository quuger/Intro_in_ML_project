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
from utils.models_manager import chatbot_model

router = Router()


class DocumentStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_model_name = State()


class SwitchModelStates(StatesGroup):
    waiting_for_model = State()


@router.message(Command("list"))
async def cmd_list(message: Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📁 Data", callback_data="list_data"),
                InlineKeyboardButton(text="🤖 Models", callback_data="list_models")
            ]
        ]
    )
    
    await message.reply("📋 Выберите категорию файлов:", reply_markup=keyboard)


@router.message(Command("switch"))
async def cmd_switch(message: Message, state: FSMContext):
    """Команда для переключения модели"""
    # Проверяем, существует ли models_map в utils
    if not hasattr(utils, 'models_map') or not utils.models_map:
        await message.reply("🤖 Нет доступных моделей для переключения.")
        return
    
    # Создаем клавиатуру с кнопками для каждой модели
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    for model_name in utils.models_map.keys():
        # Добавляем эмодзи текущей модели, если она загружена
        prefix = "✅ " if (chatbot_model.current_model_name == model_name and chatbot_model.model is not None) else ""
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"{prefix}{model_name}", 
                callback_data=f"switch_{model_name}"
            )
        ])
    
    # Добавляем кнопку отмены
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="❌ Отмена", callback_data="switch_cancel")
    ])
    
    # Получаем информацию о текущей модели
    current_model_info = ""
    if chatbot_model.current_model_name:
        current_model_info = f"\n\n📋 Текущая модель: <b>{chatbot_model.current_model_name}</b>"
    
    await message.reply(
        f"🤖 Выберите модель для загрузки:{current_model_info}",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    
    # Устанавливаем состояние ожидания выбора модели
    await state.set_state(SwitchModelStates.waiting_for_model)


@router.callback_query(F.data.startswith("switch_"), SwitchModelStates.waiting_for_model)
async def process_model_switch(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора модели"""
    model_action = callback.data.replace("switch_", "")
    
    if model_action == "cancel":
        # Отмена переключения модели
        await callback.message.edit_text(
            "❌ Переключение модели отменено.",
            reply_markup=None
        )
        await state.clear()
        await callback.answer()
        return
    
    # Извлекаем имя модели
    model_name = model_action
    
    try:
        # Загружаем модель через chatbot_model
        success = chatbot_model.load_model(model_name)
        
        if success:
            response = f"✅ Модель успешно переключена на <b>{model_name}</b>"
        else:
            response = f"❌ Не удалось загрузить модель <b>{model_name}</b>\n\nПроверьте наличие файла модели и его корректность."
        
        # Редактируем сообщение
        await callback.message.edit_text(
            response,
            parse_mode="HTML",
            reply_markup=None
        )
        
    except Exception as e:
        await callback.message.edit_text(
            f"❌ Ошибка при переключении модели: {str(e)}",
            reply_markup=None
        )
    
    # Очищаем состояние
    await state.clear()
    await callback.answer()


@router.message(Command("model_info"))
async def cmd_model_info(message: Message):
    """Команда для получения информации о текущей модели"""
    model_info = chatbot_model.get_model_info()
    
    if model_info:
        response = (
            f"🤖 <b>Информация о модели:</b>\n\n"
            f"✅ Модель загружена\n"
            f"📝 Имя модели: <b>{model_info}</b>\n"
        )
    else:
        response = (
            f"🤖 <b>Информация о модели:</b>\n\n"
            f"❌ Модель <b>не</b> загружена\n"
        )
    
    await message.reply(response, parse_mode="HTML")


@router.callback_query(F.data == "list_data")
async def show_data_files(callback: types.CallbackQuery):
    if not utils.file_map:
        await callback.message.edit_text("📭 Нет сохраненных датасетов.")
        await callback.answer()
        return
    
    response = "📋 Сохраненные файлы (Data):\n\n"
    for i, (name, path) in enumerate(utils.file_map.items(), 1):
        if os.path.exists(path):
            file_size = os.path.getsize(path)
            response += f"{i}. {name}\n"
            response += f"   📁 {os.path.basename(path)}\n"
            response += f"   📏 {file_size / 1024:.1f} KB\n\n"
        else:
            response += f"{i}. {name}\n"
            response += f"   ⚠️ Файл не найден: {path}\n\n"
    
    await callback.message.edit_text(response)
    await callback.answer()


@router.callback_query(F.data == "list_models")
async def show_models_files(callback: types.CallbackQuery):
    # Проверяем, существует ли models_map в utils
    if not hasattr(utils, 'models_map') or not utils.models_map:
        await callback.message.edit_text("🤖 Нет сохраненных моделей.")
        await callback.answer()
        return
    
    # Добавляем информацию о текущей загруженной модели
    current_model_info = ""
    if chatbot_model.current_model_name:
        current_model_info = f"\n🔹 <b>Текущая модель: {chatbot_model.current_model_name}</b>\n\n"
    
    response = f"🤖 Сохраненные модели:{current_model_info}"
    
    for i, (name, path) in enumerate(utils.models_map.items(), 1):
        if os.path.exists(path):
            file_size = os.path.getsize(path)
            # Добавляем маркер для текущей модели
            current_marker = "✅ " if name == chatbot_model.current_model_name else ""
            response += f"{i}. {current_marker}{name}\n"
            response += f"   🤖 {os.path.basename(path)}\n"
            response += f"   📏 {file_size / 1024:.1f} KB\n\n"
        else:
            response += f"{i}. {name}\n"
            response += f"   ⚠️ Файл модели не найден: {path}\n\n"
    
    await callback.message.edit_text(response, parse_mode="HTML")
    await callback.answer()


@router.message(Command("delete"))
async def cmd_delete(message: Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📁 Data", callback_data="delete_category_data"),
                InlineKeyboardButton(text="🤖 Models", callback_data="delete_category_model")
            ]
        ]
    )
    
    await message.reply("🗑️ Выберите категорию для удаления:", reply_markup=keyboard)


@router.callback_query(F.data == "delete_category_data")
async def show_data_for_deletion(callback: types.CallbackQuery):
    if not utils.file_map:
        await callback.message.edit_text("📭 Нет датасетов для удаления.")
        await callback.answer()
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    for name in utils.file_map.keys():
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text=f"❌ {name}", callback_data=f"delete_data_{name}")
        ])
    
    await callback.message.edit_text("🗑️ Выберите датасет для удаления:", reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "delete_category_model")
async def show_models_for_deletion(callback: types.CallbackQuery):
    # Проверяем, существует ли models_map в utils
    if not hasattr(utils, 'models_map') or not utils.models_map:
        await callback.message.edit_text("🤖 Нет моделей для удаления.")
        await callback.answer()
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    for name in utils.models_map.keys():
        # Не показываем кнопку удаления для текущей модели, чтобы избежать ошибок
        if name != chatbot_model.current_model_name:
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(text=f"❌ {name}", callback_data=f"delete_model_{name}")
            ])
    
    # Если после фильтрации кнопок не осталось
    if not keyboard.inline_keyboard:
        if chatbot_model.current_model_name:
            await callback.message.edit_text(
                f"⚠️ Невозможно удалить модели, так как модель '{chatbot_model.current_model_name}' "
                f"сейчас загружена и используется.\n\n"
                f"Сначала переключитесь на другую модель с помощью /switch",
                reply_markup=None
            )
        else:
            await callback.message.edit_text(
                "🤖 Нет моделей для удаления.",
                reply_markup=None
            )
    else:
        # Добавляем предупреждение, если есть загруженная модель
        warning = ""
        if chatbot_model.current_model_name:
            warning = f"\n\n⚠️ <b>Текущая модель '{chatbot_model.current_model_name}' не будет отображена для удаления.</b>"
        
        await callback.message.edit_text(
            f"🗑️ Выберите модель для удаления:{warning}",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    
    await callback.answer()


@router.callback_query(F.data.startswith("delete_data_"))
async def process_data_delete(callback: types.CallbackQuery):
    filename = callback.data.split("_", 2)[2]  # delete_data_filename
    
    if filename in utils.file_map:
        file_path = utils.file_map[filename]
        
        if os.path.exists(file_path):
            os.remove(file_path)
        
        del utils.file_map[filename]
        
        # Редактируем сообщение, чтобы убрать клавиатуру
        await callback.message.edit_text(
            f"✅ Датасет '{filename}' успешно удален.",
            reply_markup=None
        )
    else:
        # Если файл уже не найден
        await callback.message.edit_text(
            f"❌ Датасет '{filename}' не найден или уже был удален.",
            reply_markup=None
        )
    
    await callback.answer()


@router.callback_query(F.data.startswith("delete_model_"))
async def process_model_delete(callback: types.CallbackQuery):
    filename = callback.data.split("_", 2)[2]  # delete_model_filename
    
    # Проверяем, существует ли models_map
    if not hasattr(utils, 'models_map'):
        await callback.message.edit_text(
            "❌ Ошибка: словарь моделей не найден.",
            reply_markup=None
        )
        await callback.answer()
        return
    
    # Проверяем, не пытаемся ли удалить текущую модель
    if filename == chatbot_model.current_model_name:
        await callback.message.edit_text(
            f"❌ Невозможно удалить модель '{filename}', так как она сейчас загружена.\n\n"
            f"Сначала переключитесь на другую модель с помощью /switch",
            reply_markup=None
        )
        await callback.answer()
        return
    
    if filename in utils.models_map:
        file_path = utils.models_map[filename]
        
        if os.path.exists(file_path):
            os.remove(file_path)
        
        del utils.models_map[filename]
        
        await callback.message.edit_text(
            f"✅ Модель '{filename}' успешно удалена.",
            reply_markup=None
        )
    else:
        # Если файл уже не найден
        await callback.message.edit_text(
            f"❌ Модель '{filename}' не найдена или уже была удалена.",
            reply_markup=None
        )
    
    await callback.answer()


@router.message(F.document)
async def handle_document(message: Message, state: FSMContext, bot: Bot):
    doc = message.document
    
    # Проверяем расширение файла
    file_extension = None
    if doc.file_name:
        if doc.file_name.lower().endswith('.json'):
            file_extension = 'json'
        elif doc.file_name.lower().endswith('.pt'):
            file_extension = 'pt'
    
    if not file_extension:
        await message.reply(
            "❌ Неподдерживаемый формат файла. Принимаются только файлы с расширениями .json или .pt"
        )
        return
    
    # Сохраняем временный файл
    temp_dir = "temp"
    os.makedirs(temp_dir, exist_ok=True)
    temp_filename = f"temp_{message.message_id}_{doc.file_name}"
    temp_path = os.path.join(temp_dir, temp_filename)
    
    try:
        # Скачиваем файл
        file = await bot.get_file(doc.file_id)
        await bot.download_file(file.file_path, temp_path)
        
        # Обработка JSON файлов (датасеты)
        if file_extension == 'json':
            # Верифицируем JSON
            is_valid, error_msg = utils.verify_json_file(temp_path)
            
            if not is_valid:
                os.remove(temp_path)  # Удаляем временный файл
                await message.reply(f"❌ Ошибка валидации JSON: {error_msg}")
                return
            
            # Сохраняем информацию о файле в состоянии
            await state.update_data(
                temp_file_path=temp_path,
                original_filename=doc.file_name or "document.json",
                file_type='dataset'  # Указываем тип файла
            )
            
            # Запрашиваем название у пользователя
            await message.reply(
                "✅ JSON файл (датасет) прошел проверку!\n\n"
                "📝 Пожалуйста, введите название для этого датасета "
                "(без расширения .json, оно добавится автоматически):\n\n"
                "Пример: 'настройки_бота' или 'user_data'"
            )
            
            # Переходим в состояние ожидания названия датасета
            await state.set_state(DocumentStates.waiting_for_name)
        
        # Обработка PT файлов (модели)
        elif file_extension == 'pt':
            try:
                # Пробуем загрузить модель, чтобы проверить ее валидность
                import torch
                test_model = torch.load(temp_path, map_location=torch.device('cpu'), weights_only=False)
                # Если загрузка прошла успешно, файл валиден
                del test_model
                
                # Сохраняем информацию о файле в состоянии
                await state.update_data(
                    temp_file_path=temp_path,
                    original_filename=doc.file_name or "model.pt",
                    file_type='model'  # Указываем тип файла
                )
                
                # Запрашиваем название у пользователя
                await message.reply(
                    "✅ Файл модели (.pt) прошел проверку!\n\n"
                    "🤖 Пожалуйста, введите название для этой модели "
                    "(без расширения .pt, оно добавится автоматически):\n\n"
                    "Пример: 'gpt_small' или 'chatbot_v1'"
                )
                
                # Переходим в состояние ожидания названия модели
                await state.set_state(DocumentStates.waiting_for_model_name)
                
            except Exception as e:
                os.remove(temp_path)  # Удаляем временный файл
                await message.reply(f"❌ Ошибка при проверке файла модели: {str(e)}")
                return
        
    except Exception as e:
        await message.reply(f"❌ Ошибка при обработке файла: {str(e)}")
        if os.path.exists(temp_path):
            os.remove(temp_path)


@router.message(DocumentStates.waiting_for_name)
async def get_dataset_filename(message: Message, state: FSMContext):
    """Обработка ввода названия для датасета"""
    user_filename = message.text.strip()
    
    # Проверяем введенное название
    if not user_filename:
        await message.reply("❌ Название не может быть пустым. Попробуйте еще раз:")
        return
    
    if len(user_filename) > 100:
        await message.reply("❌ Название слишком длинное. Попробуйте еще раз:")
        return
    
    # Проверяем на недопустимые символы
    if re.search(r'[\\/*?!:"<>|]', user_filename):
        await message.reply(
            "❌ Название содержит недопустимые символы (\\/*?!:\"<>|). "
            "Попробуйте еще раз:"
        )
        return
    
    # Проверяем, существует ли уже датасет с таким именем
    if user_filename in utils.file_map:
        await message.reply(
            f"❌ Датасет с названием '{user_filename}' уже существует. "
            f"Пожалуйста, выберите другое название:"
        )
        return

    # Получаем данные из состояния
    data = await state.get_data()
    temp_path = data.get('temp_file_path')
    
    if not temp_path or not os.path.exists(temp_path):
        await message.reply("❌ Временный файл не найден. Отправьте файл заново.")
        await state.clear()
        return
    
    try:
        # Используем существующую функцию для сохранения датасета
        final_path = utils.save_file_to_resources(temp_path, user_filename)
        
        # Добавляем в мапу датасетов
        utils.file_map[user_filename] = final_path
        
        # Получаем информацию о файле
        file_size = os.path.getsize(temp_path)
        
        await message.reply(
            f"✅ Датасет успешно сохранен!\n\n"
            f"📝 Название: {user_filename}\n"
            f"📁 Имя файла: {os.path.basename(final_path)}\n"
            f"📏 Размер: {file_size / 1024:.1f} KB\n"
            f"📂 Путь: {final_path}\n\n"
            f"📊 Всего сохранено датасетов: {len(utils.file_map)}"
        )
        
        # Удаляем временный файл
        os.remove(temp_path)
        
    except Exception as e:
        await message.reply(f"❌ Ошибка при сохранении датасета: {str(e)}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
    
    # Очищаем состояние
    await state.clear()


@router.message(DocumentStates.waiting_for_model_name)
async def get_model_filename(message: Message, state: FSMContext):

    """Обработка ввода названия для модели"""
    user_filename = message.text.strip()
    
    # Проверяем введенное название
    if not user_filename:
        await message.reply("❌ Название не может быть пустым. Попробуйте еще раз:")
        return
    
    if len(user_filename) > 100:
        await message.reply("❌ Название слишком длинное. Попробуйте еще раз:")
        return
    
    # Проверяем на недопустимые символы
    if re.search(r'[\\/*?!:"<>|]', user_filename):
        await message.reply(
            "❌ Название содержит недопустимые символы (\\/*?!:\"<>|). "
            "Попробуйте еще раз:"
        )
        return
    
    # Проверяем, существует ли уже модель с таким именем
    if hasattr(utils, 'models_map') and user_filename in utils.models_map:
        await message.reply(
            f"❌ Модель с названием '{user_filename}' уже существует. "
            f"Пожалуйста, выберите другое название:"
        )
        return

    # Получаем данные из состояния
    data = await state.get_data()
    temp_path = data.get('temp_file_path')
    
    if not temp_path or not os.path.exists(temp_path):
        await message.reply("❌ Временный файл не найден. Отправьте файл заново.")
        await state.clear()
        return
    
    try:
        # Используем существующую функцию для сохранения модели
        final_path = utils.save_model_to_resources(temp_path, user_filename)
        
        # Добавляем в мапу моделей (убедимся, что она существует)
        if not hasattr(utils, 'models_map'):
            utils.models_map = {}
        
        utils.models_map[user_filename] = final_path
        
        # Получаем информацию о файле
        file_size = os.path.getsize(temp_path)
        
        await message.reply(
            f"✅ Модель успешно сохранена!\n\n"
            f"🤖 Название: {user_filename}\n"
            f"📁 Имя файла: {os.path.basename(final_path)}\n"
            f"📏 Размер: {file_size / 1024:.1f} KB\n"
            f"📂 Путь: {final_path}\n\n"
            f"🤖 Всего сохранено моделей: {len(utils.models_map)}\n\n"
            f"💡 Используйте /switch для загрузки этой модели"
        )
        
        # Удаляем временный файл
        os.remove(temp_path)
        
    except Exception as e:
        await message.reply(f"❌ Ошибка при сохранении модели: {str(e)}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
    
    # Очищаем состояние
    await state.clear()