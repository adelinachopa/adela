# План исправления: изображения, масштабирование, кнопка прыжка

## Текущие проблемы

### 1. Изображения не загружаются на Android
**Причина**: На Android `pygame.image.load("image/sprite/adelina.png")` не находит файлы, потому что:
- Рабочая директория не совпадает с директорией приложения
- `game_platform.py:Platform.__init__` использует `pygame.image.load(image_path)` напрямую, а не через `load_image()` из `setting.py`
- `setting.py:load_image()` уже вызывает `find_image_file()`, но это не помогает, если базовая директория не та

**Решение**:
- Добавить в `setting.py` определение `APP_PATH` — базового пути к файлам приложения на Android
- Для Android: `APP_PATH = os.environ.get('ANDROID_APP_PATH', os.path.dirname(os.path.abspath(__file__)))`
- Модифицировать `find_image_file()` чтобы искать относительно `APP_PATH`
- Исправить `game_platform.py:Platform.__init__` чтобы использовать `load_image()` вместо прямого `pygame.image.load()`

### 2. Масштабирование не работает
**Причина**: `SCREEN_WIDTH=800, SCREEN_HEIGHT=480` — это виртуальное разрешение, но реальный экран телефона может быть 1080x2400+. `pygame.SCALED` должен масштабировать, но на Android это может не работать.

**Решение**:
- Использовать `pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN | pygame.SCALED)` — это уже есть
- Проблема может быть в том, что `pygame.display.Info()` возвращает неверные данные на Android
- Добавить определение реального разрешения экрана через `pygame.display.Info()` после создания окна
- Все размеры UI (кнопки, шрифты) уже вычисляются пропорционально в `joystick.py`

### 3. Нет кнопки прыжка для Аделины
**Причина**: В `joystick.py` (старая версия) обе кнопки прыжка (`K_UP` и `K_w`) привязаны к одной `self.jump_button_pressed`.

**Решение**: Уже реализовано в новой версии `joystick.py`:
- `jump1_button_pressed` → `K_UP` (Аделина)
- `jump2_button_pressed` → `K_w` (Аня)

### 4. Изменения не попали в APK
**Причина**: Buildozer кэширует .pyc файлы. Нужно очистить кэш и пересобрать.

**Решение**: 
- Удалить `__pycache__` директории
- Удалить `.buildozer/android/platform/build-*/build/other_builds/pygame`
- Пересобрать APK

## Файлы для изменения

### 1. `setting.py` — добавить APP_PATH
```python
import sys

# Определяем базовый путь для Android
if IS_MOBILE:
    # На Android файлы находятся в директории приложения
    APP_PATH = os.path.dirname(os.path.abspath(__file__))
else:
    APP_PATH = os.getcwd()

def find_image_file(path):
    """Ищет файл с регистронезависимым сравнением, используя APP_PATH"""
    # Если путь абсолютный или файл существует, возвращаем как есть
    if os.path.isabs(path) or os.path.exists(path):
        return path
    
    # Пробуем найти относительно APP_PATH
    full_path = os.path.join(APP_PATH, path)
    if os.path.exists(full_path):
        return full_path
    
    # Регистронезависимый поиск
    dir_name = os.path.dirname(full_path)
    base_name = os.path.basename(full_path)
    
    if not os.path.exists(dir_name):
        # Пробуем относительно текущей директории
        dir_name = os.path.dirname(path)
        base_name = os.path.basename(path)
        if not os.path.exists(dir_name):
            return path
    
    try:
        for f in os.listdir(dir_name):
            if f.lower() == base_name.lower():
                return os.path.join(dir_name, f)
    except:
        pass
    
    return path
```

### 2. `game_platform.py` — использовать load_image()
```python
from setting import load_image

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, image_path, color=None):
        super().__init__()
        if image_path:
            self.image = load_image(image_path, width, height, color or GREEN)
        else:
            self.image = pygame.Surface((width, height))
            if color:
                self.image.fill(color)
            else:
                self.image.fill(GREEN)
        self.rect = self.image.get_rect(topleft=(x, y))
```

### 3. `joystick.py` — уже исправлен (отдельные кнопки прыжка + пропорциональные размеры)

### 4. `main.py` — проверить создание окна
```python
# После создания screen получить реальные размеры
if IS_MOBILE:
    info = pygame.display.Info()
    real_w, real_h = info.current_w, info.current_h
    print(f"Real screen size: {real_w}x{real_h}")
```

## Порядок действий
1. Исправить `setting.py` — добавить APP_PATH и улучшить find_image_file()
2. Исправить `game_platform.py` — использовать load_image()
3. Синхронизировать файлы с WSL
4. Очистить кэш buildozer (__pycache__)
5. Пересобрать APK
6. Установить и протестировать