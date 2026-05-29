"""
Модуль для управления сохранениями игры.
Сохраняет прогресс по уровням, количество собранных питончиков и статус завершения.
"""
import json
import os
from typing import Dict, Any

SAVE_FILE = "save.json"

def get_default_save() -> Dict[str, Any]:
    """Возвращает структуру сохранения по умолчанию."""
    return {
        "player_name": "default",
        "total_pythonchiks": 0,  # общее количество собранных питончиков за все уровни
        "levels": {
            # уровень: {"completed": bool, "collected": int, "total": int}
        }
    }

def load_save() -> Dict[str, Any]:
    """Загружает сохранение из файла. Если файла нет, возвращает сохранение по умолчанию."""
    if not os.path.exists(SAVE_FILE):
        return get_default_save()
    
    try:
        with open(SAVE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
       default = get_default_save()
        if "player_name" not in data:
            data["player_name"] = default["player_name"]
        if "total_pythonchiks" not in data:
            data["total_pythonchiks"] = default["total_pythonchiks"]
        if "levels" not in data:
            data["levels"] = default["levels"]
        return data
    except (json.JSONDecodeError, IOError) as e:
        print(f"Ошибка загрузки сохранения: {e}. Используется сохранение по умолчанию.")
        return get_default_save()

def save_game(data: Dict[str, Any]) -> bool:
    """Сохраняет данные в файл. Возвращает True при успехе."""
    try:
        with open(SAVE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except IOError as e:
        print(f"Ошибка сохранения: {e}")
        return False

def update_level_progress(level_id: str, completed: bool, collected: int, total: int) -> None:
    """
    Обновляет прогресс по уровню и общее количество питончиков.
    
    Args:
        level_id: идентификатор уровня (например, "level_01")
        completed: True если уровень пройден (активирована дверь выхода)
        collected: количество собранных питончиков на этом уровне
        total: общее количество питончиков на уровне
    """
    data = load_save()
    
    if level_id not in data["levels"]:
        data["levels"][level_id] = {"completed": False, "collected": 0, "total": total}
    
    level_data = data["levels"][level_id]
    if completed:
        level_data["completed"] = True
    if collected > level_data["collected"]:
        level_data["collected"] = collected
    level_data["total"] = total
    
    total_pythonchiks = sum(lev["collected"] for lev in data["levels"].values())
    data["total_pythonchiks"] = total_pythonchiks
    
    save_game(data)
    print(f"Прогресс уровня {level_id} обновлён: completed={completed}, collected={collected}/{total}")

def get_level_progress(level_id: str) -> Dict[str, Any]:
    """Возвращает прогресс по указанному уровню."""
    data = load_save()
    return data["levels"].get(level_id, {"completed": False, "collected": 0, "total": 0})

def get_total_pythonchiks() -> int:
    """Возвращает общее количество собранных питончиков."""
    data = load_save()
    return data.get("total_pythonchiks", 0)

def reset_save() -> None:
    """Сбрасывает сохранение до состояния по умолчанию."""
    data = get_default_save()
    save_game(data)
    print("Сохранение сброшено.")

if __name__ == "__main__":
    # Тестирование модуля
    print("Тест модуля save_manager")
    data = load_save()
    print(f"Текущее сохранение: {data}")
    update_level_progress("level_01", True, 3, 5)
    update_level_progress("level_2", False, 2, 3)
    print("После обновления:")
    print(load_save())
