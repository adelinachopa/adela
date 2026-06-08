# План исправления мобильной адаптации

## Проблемы

1. **Игра открывается в вертикальной ориентации** — хотя `buildozer.spec` указывает `orientation = landscape`, код в `main.py` определяет разрешение экрана и может получить portrait-разрешение, если телефон временно в portrait. Нужно принудительно использовать landscape-ориентацию в коде.

2. **Изображения не отображаются (белые/цветные прямоугольники)** — `load_image()` в `setting.py` использует `pygame.image.load().convert_alpha()`, который на Android может падать. Также `find_image_file()` может не находить файлы, т.к. на Android ассеты упакованы в APK и `os.path.exists()` может не работать.

3. **Текст на джойстике** — убрать все надписи снаружи кнопок ("АДЕЛИНА", "АНЯ"), оставить только "ПРЫЖОК" и "ДЕЙСТВИЕ" внутри кнопок.

## План действий

### Шаг 1: Исправить ориентацию экрана в main.py

**Файл:** `main.py` (строки 136-174)

**Проблема:** Код определяет `real_width` и `real_height` через `pygame.display.Info()`. Если телефон в portrait, `real_width < real_height`, и виртуальное разрешение получается portrait.

**Решение:** Принудительно использовать landscape-ориентацию:
- Если `real_width < real_height` (portrait), поменять их местами
- Убедиться, что virtual_width > virtual_height

**Изменения:**
```python
if IS_MOBILE:
    try:
        temp_screen = pygame.display.set_mode((1, 1), pygame.HIDDEN)
        display_info = pygame.display.Info()
        real_width = display_info.current_w
        real_height = display_info.current_h
        pygame.display.quit()
        pygame.display.init()
        
        # Принудительно landscape: если ширина меньше высоты, меняем местами
        if real_width < real_height:
            real_width, real_height = real_height, real_width
            print(f"Forced landscape: {real_width}x{real_height}")
        
        # ... остальной код
```

### Шаг 2: Исправить загрузку изображений для Android

**Файл:** `setting.py` — функция `load_image()`

**Проблема:** 
1. `pygame.image.load().convert_alpha()` может падать на Android для .jpg файлов (у них нет альфа-канала)
2. `find_image_file()` использует `os.path.exists()` который может не работать для ассетов внутри APK
3. На Android файлы находятся в `ANDROID_PRIVATE` или рядом с `sys.argv[0]`

**Решение:**
1. В `load_image()` использовать `convert()` для .jpg и `convert_alpha()` только для .png
2. В `find_image_file()` добавить прямую попытку загрузки через `pygame.image.load()` без проверки `os.path.exists()`
3. Упростить поиск: на Android пробовать пути в порядке: `APP_PATH/path`, `path`, `os.path.join(APP_PATH, "app", path)`

**Изменения в `load_image()`:**
```python
def load_image(path, width, height, default_color=(255, 255, 255)):
    if path is None:
        surface = pygame.Surface((width, height))
        surface.fill(default_color)
        return surface
    
    actual_path = find_image_file(path)
    
    try:
        img = pygame.image.load(actual_path)
        # Для .jpg используем convert(), для .png convert_alpha()
        if path.lower().endswith('.png'):
            img = img.convert_alpha()
        else:
            img = img.convert()
        return pygame.transform.scale(img, (width, height))
    except (FileNotFoundError, pygame.error) as e:
        # ... fallback
```

**Изменения в `find_image_file()`:**
```python
def find_image_file(path):
    # Если путь абсолютный, пробуем загрузить напрямую
    if os.path.isabs(path):
        return path
    
    # Прямая проверка
    if os.path.exists(path):
        return path
    
    # На Android: пробуем APP_PATH
    if APP_PATH:
        full_path = os.path.join(APP_PATH, path)
        if os.path.exists(full_path):
            return full_path
    
    # На Android: пробуем ANDROID_PRIVATE
    if 'ANDROID_PRIVATE' in os.environ:
        alt_path = os.path.join(os.environ['ANDROID_PRIVATE'], path)
        if os.path.exists(alt_path):
            return alt_path
    
    # На Android: пробуем путь относительно sys.argv[0]
    if IS_MOBILE:
        try:
            base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
            alt_path = os.path.join(base_dir, path)
            if os.path.exists(alt_path):
                return alt_path
        except:
            pass
    
    # Регистронезависимый поиск (как было)
    # ...
    
    return path
```

### Шаг 3: Исправить текст на джойстике

**Файл:** `joystick.py` — метод `draw()` (строки 359-431)

**Проблема:** Снаружи кнопок рисуются надписи "АДЕЛИНА", "АНЯ", а на кнопках — "ПРЫЖОК" и "ДЕЙСТВИЕ". Нужно убрать внешние надписи, оставить только "ПРЫЖОК" и "ДЕЙСТВИЕ" внутри кнопок.

**Решение:** Удалить строки, рисующие текст снаружи кнопок (строки 378-381, 398-401, 422-431). Оставить только текст внутри кнопок (строки 383-387, 403-406, 418-420).

### Шаг 4: Пересобрать APK

1. Синхронизировать изменённые файлы в WSL
2. Запустить сборку
3. Скопировать APK в Windows