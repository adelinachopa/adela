import pygame
import os
import sys


IS_MOBILE = False

# Эталонное разрешение (ПК)
REFERENCE_WIDTH = 1280
REFERENCE_HEIGHT = 720

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720

FPS = 60

IMG_PATH = "image/"
SPRITE_PATH = IMG_PATH + "sprite/"

PLAYER1_IMG = SPRITE_PATH + "adelina.png"   # Аделина
PLAYER2_IMG = SPRITE_PATH + "anna.png"   # Аня
ENEMY_IMG = SPRITE_PATH + "dima.png" # Дима

BACKGROUND_IMG = IMG_PATH + "background/level1.jpg"
PLATFORM_TEX = IMG_PATH + "platform/grass1.jpg"


# Коэффициент масштабирования для объектов уровня
# Отношение текущего разрешения к эталонному (1280x720)
SCALE_FACTOR = SCREEN_WIDTH / REFERENCE_WIDTH

# Размер блока по умолчанию
BLOCK_SIZE = 40  # Стандартный размер для ПК


def find_image_file(path):
    """
    Ищет файл изображения с регистронезависимым сравнением.
    На некоторых системах файловая система регистрозависима, поэтому эта функция
    ищет файл, игнорируя регистр.
    
    Args:
        path (str): Путь к файлу изображения (относительный или абсолютный)
        
    Returns:
        str: Реальный путь к файлу или исходный путь, если файл не найден
    """
    # Если путь абсолютный, возвращаем как есть
    if os.path.isabs(path):
        return path
    
    # Прямая проверка в текущей директории
    if os.path.exists(path):
        return path
    
    # Пробуем относительно рабочей директории
    cwd_path = os.path.join(os.getcwd(), path)
    if os.path.exists(cwd_path):
        return cwd_path
    
    # Регистронезависимый поиск
    dir_name = os.path.dirname(path)
    base_name = os.path.basename(path)
    if os.path.exists(dir_name):
        try:
            for f in os.listdir(dir_name):
                if f.lower() == base_name.lower():
                    return os.path.join(dir_name, f)
        except:
            pass
    
    # Регистронезависимый поиск относительно CWD
    cwd_dir = os.path.join(os.getcwd(), dir_name)
    if os.path.exists(cwd_dir):
        try:
            for f in os.listdir(cwd_dir):
                if f.lower() == base_name.lower():
                    return os.path.join(cwd_dir, f)
        except:
            pass
    
    return path  # Файл не найден, возвращаем исходный путь


def load_image(path, width, height, default_color=(255, 255, 255)):
    """
    Безопасно загружает изображение и масштабирует его.
    Использует регистронезависимый поиск файла.
    
    Args:
        path (str): Путь к файлу изображения
        width (int): Ширина для масштабирования
        height (int): Высота для масштабирования
        default_color (tuple): Цвет по умолчанию если загрузка не удалась
    
    Returns:
        pygame.Surface: Масштабированное изображение или цветная поверхность
    """
    if path is None:
        surface = pygame.Surface((width, height))
        surface.fill(default_color)
        return surface
    
    # Список путей для попытки загрузки (по порядку)
    paths_to_try = []
    
    # 1. Исходный путь (как есть)
    paths_to_try.append(path)
    
    # 2. Абсолютный путь через CWD
    paths_to_try.append(os.path.abspath(path))
    
    # 3. Через find_image_file (регистронезависимый поиск)
    found_path = find_image_file(path)
    if found_path != path:
        paths_to_try.append(found_path)
        paths_to_try.append(os.path.abspath(found_path))
    
    # 4. CWD + путь
    cwd = os.getcwd()
    paths_to_try.append(os.path.join(cwd, path))
    
    # Пробуем каждый путь
    last_error = None
    tried_paths = []
    for try_path in paths_to_try:
        tried_paths.append(try_path)
        try:
            img = pygame.image.load(try_path)
            return pygame.transform.scale(img, (width, height))
        except (FileNotFoundError, pygame.error) as e:
            last_error = e
            continue
    
    # Все пути не сработали — выводим информацию для отладки
    error_msg = f"IMAGE LOAD FAILED: '{path}' ({width}x{height})"
    print(f"=== {error_msg} ===")
    print(f"Tried paths ({len(tried_paths)}):")
    for i, tp in enumerate(tried_paths):
        exists = os.path.exists(tp)
        print(f"  {i+1}. {tp} (exists={exists})")
    print(f"Last error: {last_error}")
    
    # Также пишем в game_errors.log
    from datetime import datetime
    try:
        with open("game_errors.log", "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] {error_msg}\n")
            for tp in tried_paths:
                f.write(f"  Tried: {tp}\n")
    except:
        pass
    
    surface = pygame.Surface((width, height))
    surface.fill(default_color)
    return surface


BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0, 100, 255)    
RED = (255, 100, 100)   
GREEN = (100, 255, 100) 
GRAY = (150, 150, 150)  

GRAVITY = 0.5
MAX_FALL_SPEED = 15
BOUNCE_FACTOR = -0.5  # коэффициент отскока (отрицательный для обратного направления)
COLLISION_EPSILON = 4  # увеличенный отступ для стабильности (уменьшает тряску)

PLAYER_WIDTH = 70
PLAYER_HEIGHT = 100
ENEMY_SIZE = 40

PLAYER_SPEED = 5
JUMP_POWER = -10
ENEMY_SPEED = 2
