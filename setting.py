import pygame
import os
import sys


# ПК-версия: IS_MOBILE всегда False
IS_MOBILE = False

# Эталонное разрешение (ПК)
REFERENCE_WIDTH = 1280
REFERENCE_HEIGHT = 720

# Размеры экрана
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720

FPS = 60

# Определяем базовый путь к файлам приложения
APP_PATH = None
try:
    APP_PATH = os.path.dirname(os.path.abspath(__file__))
except:
    APP_PATH = os.getcwd()

if APP_PATH is None:
    APP_PATH = os.getcwd()


IMG_PATH = "image/"
SPRITE_PATH = IMG_PATH + "sprite/"

PLAYER1_IMG = SPRITE_PATH + "adelina.png"   # Аделина
PLAYER2_IMG = SPRITE_PATH + "anna.png"   # Аня
ENEMY_IMG = SPRITE_PATH + "dima.png" # Дима

BACKGROUND_IMG = IMG_PATH + "background/level1.jpg"
PLATFORM_TEX = IMG_PATH + "platform/grass1.jpg"


# Коэффициент масштабирования (для ПК всегда 1.0)
SCALE_FACTOR = 1.0

# Размер блока для ПК
BLOCK_SIZE = 40


def find_image_file(path):
    """
    Ищет файл изображения. На ПК просто проверяет существование файла.
    
    Args:
        path (str): Путь к файлу изображения (относительный или абсолютный)
        
    Returns:
        str: Реальный путь к файлу или исходный путь, если файл не найден
    """
    if os.path.isabs(path):
        return path
    
    if os.path.exists(path):
        return path
    
    # Пробуем относительно APP_PATH
    if APP_PATH:
        full_path = os.path.join(APP_PATH, path)
        if os.path.exists(full_path):
            return full_path
    
    # Пробуем относительно CWD
    cwd_path = os.path.join(os.getcwd(), path)
    if os.path.exists(cwd_path):
        return cwd_path
    
    return path  # Файл не найден, возвращаем исходный путь


def load_image(path, width, height, default_color=(255, 255, 255)):
    """
    Загружает изображение и масштабирует его.
    
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
    
    # Пробуем загрузить изображение
    try:
        img = pygame.image.load(path)
        try:
            if path.lower().endswith('.png'):
                img = img.convert_alpha()
            else:
                img = img.convert()
        except:
            pass
        return pygame.transform.scale(img, (width, height))
    except (FileNotFoundError, pygame.error):
        pass
    
    # Если не удалось, пробуем через find_image_file
    found_path = find_image_file(path)
    if found_path != path:
        try:
            img = pygame.image.load(found_path)
            try:
                if path.lower().endswith('.png'):
                    img = img.convert_alpha()
                else:
                    img = img.convert()
            except:
                pass
            return pygame.transform.scale(img, (width, height))
        except (FileNotFoundError, pygame.error):
            pass
    
    # Все пути не сработали — создаём поверхность по умолчанию
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


# Размеры персонажей (базовые для ПК 1280x720)
PLAYER_WIDTH = 70
PLAYER_HEIGHT = 100
ENEMY_SIZE = 40

PLAYER_SPEED = 5
JUMP_POWER = -10
ENEMY_SPEED = 2
