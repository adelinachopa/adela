import pygame
import os
import sys


# Определение мобильной платформы
# НЕ вызываем pygame.display.Info() здесь — дисплей ещё не инициализирован!
# Используем только переменные окружения
IS_MOBILE = False
try:
    if os.environ.get('ANDROID_ARGUMENT') or os.environ.get('IOS_SIMULATOR'):
        IS_MOBILE = True
    # Дополнительная проверка: на Android ANDROID_PRIVATE всегда установлен
    if 'ANDROID_PRIVATE' in os.environ:
        IS_MOBILE = True
    # На Android sys.argv[0] содержит путь к main.py
    if IS_MOBILE is False and sys.platform == 'linux':
        try:
            if 'android' in sys.argv[0].lower() or 'com.termux' in sys.argv[0].lower():
                IS_MOBILE = True
        except:
            pass
except:
    pass

# Эталонное разрешение (ПК)
REFERENCE_WIDTH = 1280
REFERENCE_HEIGHT = 720

# Размеры экрана по умолчанию (могут быть переопределены в main.py)
# На мобильных устройствах определяются динамически через pygame.display.Info()
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720

FPS = 60

# Определяем базовый путь к файлам приложения
# На Android рабочая директория может не совпадать с директорией приложения
APP_PATH = None

# 1. Android private storage (наиболее надёжный для pygame APK)
if 'ANDROID_PRIVATE' in os.environ:
    APP_PATH = os.environ['ANDROID_PRIVATE']
# 2. Android app path
elif 'ANDROID_APP_PATH' in os.environ:
    APP_PATH = os.environ['ANDROID_APP_PATH']
# 3. Frozen app (pyinstaller, etc.)
elif getattr(sys, 'frozen', False):
    APP_PATH = os.path.dirname(sys.executable)
# 4. Android через sys.argv[0] (наиболее вероятный путь для pygame APK)
elif IS_MOBILE:
    try:
        APP_PATH = os.path.dirname(os.path.abspath(sys.argv[0]))
    except:
        APP_PATH = os.getcwd()
# 5. Fallback: директория скрипта
else:
    try:
        APP_PATH = os.path.dirname(os.path.abspath(__file__))
    except:
        APP_PATH = os.getcwd()

# Если APP_PATH всё ещё None, используем os.getcwd()
if APP_PATH is None:
    APP_PATH = os.getcwd()


# ============================================================
# Логирование для Android (вывод в logcat и в файл)
# ============================================================
_android_log_file = None

def _get_log_path():
    """Возвращает путь к файлу лога (в ANDROID_PRIVATE если доступно)"""
    if 'ANDROID_PRIVATE' in os.environ:
        return os.path.join(os.environ['ANDROID_PRIVATE'], 'game_debug.log')
    return os.path.join(os.getcwd(), 'game_debug.log')

def android_log(msg, tag="PYGAME"):
    """Выводит сообщение в logcat (Android) и в файл.
    На Android print() не виден в logcat, поэтому используем os.system('log').
    """
    # 1. Пытаемся использовать android модуль (из p4a)
    try:
        import android
        android.log(msg, tag=tag)
    except ImportError:
        pass
    
    # 2. Пытаемся использовать log через os.system (работает на Android)
    try:
        os.system(f'log -t "{tag}" "{msg}"')
    except:
        pass
    
    # 3. Пишем в файл (можно прочитать через adb)
    try:
        log_path = _get_log_path()
        with open(log_path, 'a', encoding='utf-8') as f:
            from datetime import datetime
            f.write(f"[{datetime.now().strftime('%H:%M:%S')}] [{tag}] {msg}\n")
    except:
        pass
    
    # 4. Также пишем в stdout (на случай если кто-то смотрит)
    try:
        print(f"[{tag}] {msg}")
        sys.stdout.flush()
    except:
        pass


# Выводим начальную отладочную информацию
android_log(f"APP_PATH: {APP_PATH}", "INIT")
android_log(f"IS_MOBILE: {IS_MOBILE}", "INIT")
android_log(f"SCREEN: {SCREEN_WIDTH}x{SCREEN_HEIGHT}", "INIT")
android_log(f"CWD: {os.getcwd()}", "INIT")
android_log(f"ANDROID_PRIVATE: {os.environ.get('ANDROID_PRIVATE', 'NOT SET')}", "INIT")
android_log(f"sys.argv[0]: {sys.argv[0] if len(sys.argv) > 0 else 'N/A'}", "INIT")
android_log(f"sys.platform: {sys.platform}", "INIT")

# Список файлов в ANDROID_PRIVATE
if 'ANDROID_PRIVATE' in os.environ:
    priv = os.environ['ANDROID_PRIVATE']
    try:
        files = os.listdir(priv)
        android_log(f"Files in ANDROID_PRIVATE ({len(files)}):", "INIT")
        for f in sorted(files):
            android_log(f"  {f}", "INIT")
    except Exception as e:
        android_log(f"Cannot list ANDROID_PRIVATE: {e}", "INIT")

# Список файлов в CWD
try:
    cwd_files = os.listdir(os.getcwd())
    android_log(f"Files in CWD ({len(cwd_files)}):", "INIT")
    for f in sorted(cwd_files):
        android_log(f"  {f}", "INIT")
except Exception as e:
    android_log(f"Cannot list CWD: {e}", "INIT")


IMG_PATH = "image/"
SPRITE_PATH = IMG_PATH + "sprite/"

PLAYER1_IMG = SPRITE_PATH + "adelina.png"   # Аделина
PLAYER2_IMG = SPRITE_PATH + "anna.png"   # Аня
ENEMY_IMG = SPRITE_PATH + "dima.png" # Дима
# PLATFORM_IMG = SPRITE_PATH + "platform.png"

BACKGROUND_IMG = IMG_PATH + "background/level1.jpg"
PLATFORM_TEX = IMG_PATH + "platform/grass1.jpg"


# Коэффициент масштабирования для объектов уровня
# Отношение текущего разрешения к эталонному (1280x720)
SCALE_FACTOR = SCREEN_WIDTH / REFERENCE_WIDTH

# Размер блока по умолчанию
if IS_MOBILE:
    BLOCK_SIZE = int(SCREEN_WIDTH * 0.05)  # 5% от ширины экрана
else:
    BLOCK_SIZE = 40  # Стандартный размер для ПК


def find_image_file(path):
    """
    Ищет файл изображения с регистронезависимым сравнением.
    На Android файловая система регистрозависима, поэтому эта функция
    ищет файл, игнорируя регистр. Также учитывает APP_PATH.
    
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
    
    # Список базовых директорий для поиска
    base_dirs = []
    if APP_PATH:
        base_dirs.append(APP_PATH)
    if 'ANDROID_PRIVATE' in os.environ:
        base_dirs.append(os.environ['ANDROID_PRIVATE'])
    if IS_MOBILE:
        try:
            base_dirs.append(os.path.dirname(os.path.abspath(sys.argv[0])))
        except:
            pass
    base_dirs.append(os.getcwd())
    
    # Убираем дубликаты
    seen = set()
    unique_dirs = []
    for d in base_dirs:
        if d and d not in seen:
            seen.add(d)
            unique_dirs.append(d)
    
    # Пробуем каждый базовый путь
    for base in unique_dirs:
        full_path = os.path.join(base, path)
        if os.path.exists(full_path):
            return full_path
        
        # Регистронезависимый поиск
        dir_name = os.path.dirname(full_path)
        base_name = os.path.basename(path)
        if os.path.exists(dir_name):
            try:
                for f in os.listdir(dir_name):
                    if f.lower() == base_name.lower():
                        return os.path.join(dir_name, f)
            except:
                pass
    
    return path  # Файл не найден, возвращаем исходный путь


def load_image(path, width, height, default_color=(255, 255, 255)):
    """
    Безопасно загружает изображение и масштабирует его.
    На Android использует регистронезависимый поиск файла и APP_PATH.
    
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
    
    # 2. Абсолютный путь через CWD (ВАЖНО: pygame.image.load() на Android/SDL2
    #    может не работать с относительными путями, используем os.path.abspath)
    paths_to_try.append(os.path.abspath(path))
    
    # 3. Через find_image_file (регистронезависимый поиск)
    found_path = find_image_file(path)
    if found_path != path:
        paths_to_try.append(found_path)
        paths_to_try.append(os.path.abspath(found_path))
    
    # 4. На Android: CWD + путь (рабочая директория = ANDROID_PRIVATE/app/)
    cwd = os.getcwd()
    paths_to_try.append(os.path.join(cwd, path))
    
    # 5. На Android: ANDROID_PRIVATE + путь
    if 'ANDROID_PRIVATE' in os.environ:
        priv = os.environ['ANDROID_PRIVATE']
        paths_to_try.append(os.path.join(priv, path))
        # Также ANDROID_PRIVATE + /app + путь (реальная структура на Android)
        paths_to_try.append(os.path.join(priv, 'app', path))
    
    # 6. На Android: APP_PATH + путь
    if APP_PATH:
        paths_to_try.append(os.path.join(APP_PATH, path))
    
    # 7. На Android: путь относительно sys.argv[0]
    if IS_MOBILE:
        try:
            base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
            paths_to_try.append(os.path.join(base_dir, path))
        except:
            pass
    
    # 8. На Android: пробуем просто имя файла (без пути) в ANDROID_PRIVATE
    if IS_MOBILE and 'ANDROID_PRIVATE' in os.environ:
        base_name = os.path.basename(path)
        priv = os.environ['ANDROID_PRIVATE']
        paths_to_try.append(os.path.join(priv, base_name))
        paths_to_try.append(os.path.join(priv, 'app', base_name))
    
    # Пробуем каждый путь
    last_error = None
    tried_paths = []
    for try_path in paths_to_try:
        tried_paths.append(try_path)
        try:
            # Сначала пробуем загрузить без convert (максимальная совместимость)
            img = pygame.image.load(try_path)
            # Пробуем convert, но если не получается — используем как есть
            try:
                if path.lower().endswith('.png'):
                    img = img.convert_alpha()
                else:
                    img = img.convert()
            except:
                pass  # Используем изображение как есть
            return pygame.transform.scale(img, (width, height))
        except (FileNotFoundError, pygame.error) as e:
            last_error = e
            continue
    
    # Если pygame.image.load не сработал ни с одним путём,
    # пробуем загрузить через Python open() + BytesIO (работает на Android,
    # где SDL2 RWops может не поддерживать прямые пути к файлам)
    if IS_MOBILE:
        for try_path in paths_to_try:
            try:
                if os.path.exists(try_path):
                    with open(try_path, 'rb') as f:
                        file_data = f.read()
                    import io
                    img = pygame.image.load(io.BytesIO(file_data))
                    try:
                        if path.lower().endswith('.png'):
                            img = img.convert_alpha()
                        else:
                            img = img.convert()
                    except:
                        pass
                    return pygame.transform.scale(img, (width, height))
            except Exception as e:
                last_error = e
                continue
    
    # Все пути не сработали — выводим подробную информацию для отладки
    error_msg = f"IMAGE LOAD FAILED: '{path}' ({width}x{height})"
    android_log(f"=== {error_msg} ===", "IMG_FAIL")
    android_log(f"Tried paths ({len(tried_paths)}):", "IMG_FAIL")
    for i, tp in enumerate(tried_paths):
        exists = os.path.exists(tp)
        android_log(f"  {i+1}. {tp} (exists={exists})", "IMG_FAIL")
    android_log(f"Last error: {last_error}", "IMG_FAIL")
    android_log(f"APP_PATH={APP_PATH}", "IMG_FAIL")
    android_log(f"ANDROID_PRIVATE={os.environ.get('ANDROID_PRIVATE', 'NOT SET')}", "IMG_FAIL")
    android_log(f"CWD={os.getcwd()}", "IMG_FAIL")
    android_log(f"IS_MOBILE={IS_MOBILE}", "IMG_FAIL")
    
    # На Android: выводим список файлов в ANDROID_PRIVATE для отладки
    if 'ANDROID_PRIVATE' in os.environ:
        priv = os.environ['ANDROID_PRIVATE']
        android_log(f"Files in ANDROID_PRIVATE ({priv}):", "IMG_FAIL")
        try:
            for f in os.listdir(priv):
                android_log(f"  {f}", "IMG_FAIL")
        except Exception as e2:
            android_log(f"  Cannot list: {e2}", "IMG_FAIL")
    
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
# JUMP_POWER = -12
# PLAYER_SPEED = 5
# ENEMY_SPEED = 2


# Размеры персонажей (базовые для ПК 1280x720)
# На мобильных масштабируются через SCALE_FACTOR в levels.py
PLAYER_WIDTH = 70
PLAYER_HEIGHT = 100
ENEMY_SIZE = 40

MOBILE_JOYSTICK_RADIUS = 60
MOBILE_BUTTON_RADIUS = 50
MOBILE_MARGIN = 80

PLAYER_SPEED = 5
JUMP_POWER = -10
ENEMY_SPEED = 2
