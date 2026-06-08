# План адаптации для мобильных устройств

## Проблемы и решения

### 1. Изображения не загружаются (белый экран на заставке)
**Причина**: `APP_PATH` в `setting.py` неправильно определяется на Android.

**Решение**: 
- Добавить fallback-пути: `ANDROID_PRIVATE`, `ANDROID_APP_PATH`, `os.path.dirname(os.path.abspath(sys.argv[0]))`
- В `find_image_file()` добавить поиск по всем возможным базовым путям

### 2. Кнопка "действие" Аделины слишком далеко от джойстика
**Решение**: 
- Кнопка действия — справа от левого джойстика (Аделина)
- Кнопка прыжка Аделины — слева от левого джойстика
- Кнопка прыжка Ани — справа от правого джойстика

### 3. Блоки слишком большие для мобильного экрана
**Решение**: 
- Базовый размер блока = 5% от ширины экрана
- Ввести `SCALE_FACTOR` для всех размеров

### 4. Адаптивный размер под реальное разрешение
**Решение**:
- Определять реальное разрешение экрана через `pygame.display.Info()`
- Вычислять виртуальное разрешение с сохранением пропорций 16:9
- Использовать `pygame.FULLSCREEN | pygame.SCALED`

## Детальный план реализации

### Шаг 1: Исправить определение APP_PATH для Android
**Файл**: `setting.py`

```python
# Определяем базовый путь к файлам приложения
APP_PATH = None

# 1. Android private storage
if 'ANDROID_PRIVATE' in os.environ:
    APP_PATH = os.environ['ANDROID_PRIVATE']
# 2. Android app path
elif 'ANDROID_APP_PATH' in os.environ:
    APP_PATH = os.environ['ANDROID_APP_PATH']
# 3. Frozen app (pyinstaller, etc.)
elif getattr(sys, 'frozen', False):
    APP_PATH = os.path.dirname(sys.executable)
# 4. Android через sys.argv[0]
elif IS_MOBILE:
    APP_PATH = os.path.dirname(os.path.abspath(sys.argv[0]))
# 5. Fallback: директория скрипта
else:
    try:
        APP_PATH = os.path.dirname(os.path.abspath(__file__))
    except:
        APP_PATH = os.getcwd()
```

В `find_image_file()` добавить поиск по всем возможным путям, включая `os.getcwd()`.

### Шаг 2: Добавить глобальный SCALE_FACTOR
**Файл**: `setting.py`

```python
REFERENCE_WIDTH = 1280
REFERENCE_HEIGHT = 720

# Виртуальное разрешение для мобильных
if IS_MOBILE:
    SCREEN_WIDTH = 800
    SCREEN_HEIGHT = 480
else:
    SCREEN_WIDTH = 1280
    SCREEN_HEIGHT = 720

# Коэффициент масштабирования для объектов уровня
SCALE_FACTOR = SCREEN_WIDTH / REFERENCE_WIDTH

# Размеры блоков и объектов
if IS_MOBILE:
    BLOCK_SIZE = int(SCREEN_WIDTH * 0.05)  # 5% от ширины экрана
    PLAYER_WIDTH = int(50 * SCALE_FACTOR)
    PLAYER_HEIGHT = int(70 * SCALE_FACTOR)
    ENEMY_SIZE = int(30 * SCALE_FACTOR)
else:
    BLOCK_SIZE = 40
    PLAYER_WIDTH = 70
    PLAYER_HEIGHT = 100
    ENEMY_SIZE = 40
```

### Шаг 3: Масштабировать уровни при загрузке
**Файл**: `levels.py` (метод `load_level`)

При загрузке каждого объекта из JSON умножать координаты и размеры на `SCALE_FACTOR`:
- `x`, `y` — умножать на `SCALE_FACTOR`
- `width`, `height` — умножать на `SCALE_FACTOR`
- Для блоков: если размер не указан, использовать `BLOCK_SIZE`
- Для игроков: если размер не указан, использовать `PLAYER_WIDTH/HEIGHT`

### Шаг 4: Исправить расположение кнопок в joystick.py
**Файл**: `joystick.py`

Новая схема расположения (для мобильных):
```
[Кнопка прыжка Аделины] [Джойстик Аделины] [Кнопка действия] ... [Джойстик Ани] [Кнопка прыжка Ани]
```

- **Джойстик Аделины** — слева внизу (как сейчас)
- **Кнопка прыжка Аделины** — слева от джойстика Аделины (на расстоянии 2.5 радиуса кнопки)
- **Кнопка действия** — справа от джойстика Аделины (на расстоянии 2.5 радиуса кнопки)
- **Джойстик Ани** — справа внизу (как сейчас)
- **Кнопка прыжка Ани** — справа от джойстика Ани

### Шаг 5: Адаптивное разрешение экрана
**Файл**: `main.py` и `setting.py`

В `main.py`:
```python
# Получаем реальное разрешение ДО создания окна
# (используем тестовое окно или Info)
if IS_MOBILE:
    # Создаём временное окно для получения реального разрешения
    temp_screen = pygame.display.set_mode((1, 1))
    display_info = pygame.display.Info()
    real_w = display_info.current_w
    real_h = display_info.current_h
    pygame.display.quit()
    
    # Вычисляем виртуальное разрешение с сохранением пропорций
    # База: 800x480, но масштабируем под реальное разрешение
    scale = min(real_w / 800, real_h / 480)
    SCREEN_WIDTH = int(800 * scale)
    SCREEN_HEIGHT = int(480 * scale)
```

### Шаг 6: Пересобрать APK
- Запустить buildozer
- Скопировать APK на Windows
- Протестировать на телефоне

## Схема расположения элементов управления (мобильный экран)

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│                                                     │
│                                                     │
│                                                     │
│                                                     │
│                                                     │
│                                                     │
│                                                     │
│                                                     │
│  [ПРЫЖОК]  [ДЖОЙСТИК]  [ДЕЙСТВИЕ]    [ДЖОЙСТИК] [ПРЫЖОК] │
│  АДЕЛИНА   АДЕЛИНА                  АНЯ        АНЯ      │
└─────────────────────────────────────────────────────┘
```

## Файлы для изменения

| Файл | Изменения |
|------|-----------|
| `setting.py` | APP_PATH, SCALE_FACTOR, BLOCK_SIZE, адаптивные размеры |
| `levels.py` | Масштабирование координат и размеров при загрузке |
| `joystick.py` | Перерасположение кнопок |
| `main.py` | Адаптивное разрешение экрана |