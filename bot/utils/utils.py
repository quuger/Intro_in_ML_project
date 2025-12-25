import shutil
from jsonschema import validate
from config import config
import os
import json
import uuid

RESOURCES_DIR = config.resources_dir
MODELS_DIR = config.models_dir
file_map = {}
models_map = {}

def validate_json_structure(json_content: dict, schema: dict = None) -> tuple[bool, str]:
    """
    Валидирует структуру JSON по схеме
    """
    if schema is None:
        # Базовая схема для проверки
        schema = {
            "type": "object",
            "properties": {
                "version": {"type": "string"},
                "data": {"type": "array"}
            },
            "required": ["version"]
        }
    
    try:
        validate(instance=json_content, schema=schema)
        return True, "JSON соответствует схеме"
    except ImportError:
        return True, "Модуль jsonschema не установлен, проверка схемы пропущена"
    except Exception as e:
        return False, f"Ошибка в структуре JSON: {str(e)}"



def verify_json_file(file_path: str) -> tuple[bool, str]:
    """
    Проверяет, является ли файл валидным JSON
    
    Args:
        file_path: путь к файлу
        
    Returns:
        tuple: (is_valid: bool, error_message: str)
    """
    try:        
        # Проверяем размер файла
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            return False, "Файл пустой"
        if file_size > 20 * 1024 * 1024:  # 20 MB лимит
            return False, "Файл слишком большой (максимум 20 MB)"
        
        # Пытаемся загрузить и проверить JSON
        with open(file_path, 'r', encoding='utf-8') as f:
            json_content = json.load(f)
        
        # Дополнительная проверка структуры JSON
        if not isinstance(json_content, (dict, list)):
            return False, "JSON должен быть объектом или массивом"
        
        return True, "JSON файл валиден"
        
    except json.JSONDecodeError as e:
        return False, f"Ошибка в структуре JSON: {str(e)}"
    except UnicodeDecodeError:
        return False, "Некорректная кодировка файла. Используйте UTF-8"
    except Exception as e:
        return False, f"Неизвестная ошибка: {str(e)}"


def save_file_to_resources(source_path: str, user_filename: str) -> str:
    os.makedirs(RESOURCES_DIR, exist_ok=True)

    file_uuid = str(uuid.uuid4())[:8]
    new_filename = f"{user_filename}_{file_uuid}.json"
    target_path = os.path.join(RESOURCES_DIR, new_filename)
    shutil.copy2(source_path, target_path)
    print(f"Файл сохранен: {user_filename} -> {target_path}")
    return target_path


def save_file_map():
    """Сохраняет мапу файлов в JSON файл"""
    os.makedirs(RESOURCES_DIR, exist_ok=True)
    map_path = os.path.join(RESOURCES_DIR, "file_map.json")
    # Преобразуем пути в строки для сериализации
    serializable_map = {k: v for k, v in file_map.items()}
    with open(map_path, 'w', encoding='utf-8') as f:
        json.dump(serializable_map, f, ensure_ascii=False, indent=2)


def load_file_map():
    """Загружает мапу файлов из JSON файла"""
    map_path = os.path.join(RESOURCES_DIR, "file_map.json")
    if os.path.exists(map_path):
        with open(map_path, 'r', encoding='utf-8') as f:
            loaded = json.load(f)
            # Восстанавливаем абсолютные пути
            for k, v in loaded.items():
                file_map[k] = v


def save_model_to_resources(source_path: str, user_filename: str) -> str:
    """Сохраняет файл модели в resources"""
    os.makedirs(MODELS_DIR, exist_ok=True)

    file_uuid = str(uuid.uuid4())[:8]
    # Определяем расширение файла
    _, ext = os.path.splitext(source_path)
    new_filename = f"{user_filename}_{file_uuid}{ext}"
    target_path = os.path.join(MODELS_DIR, new_filename)
    shutil.copy2(source_path, target_path)
    print(f"Модель сохранена: {user_filename} -> {target_path}")
    return target_path


def save_models_map():
    """Сохраняет мапу моделей в JSON файл"""
    os.makedirs(MODELS_DIR, exist_ok=True)
    map_path = os.path.join(MODELS_DIR, "models_map.json")
    # Преобразуем пути в строки для сериализации
    serializable_map = {k: v for k, v in models_map.items()}
    with open(map_path, 'w', encoding='utf-8') as f:
        json.dump(serializable_map, f, ensure_ascii=False, indent=2)


def load_models_map():
    """Загружает мапу моделей из JSON файла"""
    map_path = os.path.join(MODELS_DIR, "models_map.json")
    if os.path.exists(map_path):
        with open(map_path, 'r', encoding='utf-8') as f:
            loaded = json.load(f)
            # Восстанавливаем абсолютные пути
            for k, v in loaded.items():
                models_map[k] = v

                
def save_all_maps():
    save_file_map()
    save_models_map()


def load_all_maps():
    load_file_map()
    load_models_map()