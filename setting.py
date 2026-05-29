import pygame
import os


IS_MOBILE = False
try:
    if os.environ.get('ANDROID_ARGUMENT') or os.environ.get('IOS_SIMULATOR'):
        IS_MOBILE = True
    info = pygame.display.Info()
    if info.current_w <= 1024 or info.current_h <= 600:
        IS_MOBILE = True
except:
    pass

if IS_MOBILE:
    SCREEN_WIDTH = 800
    SCREEN_HEIGHT = 480
else:
    SCREEN_WIDTH = 1280
    SCREEN_HEIGHT = 720

FPS = 60

IMG_PATH = "image/"
SPRITE_PATH = IMG_PATH + "sprite/"

PLAYER1_IMG = SPRITE_PATH + "adelina.png"   # Аделина
PLAYER2_IMG = SPRITE_PATH + "anna.png"   # Аня
ENEMY_IMG = SPRITE_PATH + "dima.png" # Дима
# PLATFORM_IMG = SPRITE_PATH + "platform.png"

BACKGROUND_IMG = IMG_PATH + "background/level1.jpg"
PLATFORM_TEX = IMG_PATH + "platform/grass1.jpg"

def load_image(path, width, height, default_color=(255, 255, 255)):
    """
    Безопасно загружает изображение и масштабирует его.
    
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
    
    try:
        img = pygame.image.load(path).convert_alpha()
        return pygame.transform.scale(img, (width, height))
    except (FileNotFoundError, pygame.error) as e:
        error_msg = f"Warning: Could not load image '{path}'. Error: {e}"
        print(error_msg)
        
        from datetime import datetime
        try:
            with open("game_errors.log", "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now()}] {error_msg}\n")
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
# JUMP_POWER = -12
# PLAYER_SPEED = 5
# ENEMY_SPEED = 2


if IS_MOBILE:
    PLAYER_WIDTH = 50
    PLAYER_HEIGHT = 70
    ENEMY_SIZE = 30
else:
    PLAYER_WIDTH = 70
    PLAYER_HEIGHT = 100
    ENEMY_SIZE = 40

MOBILE_JOYSTICK_RADIUS = 60
MOBILE_BUTTON_RADIUS = 50
MOBILE_MARGIN = 80

if IS_MOBILE:
    PLAYER_SPEED = 4
    JUMP_POWER = -9
    ENEMY_SPEED = 1.5
else:
    PLAYER_SPEED = 5
    JUMP_POWER = -10
    ENEMY_SPEED = 2
