# План переноса ПК-адаптации из escape to EMK в pk_orig

## Цель
Перенести улучшения для ПК-версии из проекта `escape to EMK` в `pk_orig`. Адаптация касается только ПК-функционала (мобильные части НЕ переносятся).

## Изменения по файлам

### 1. setting.py — улучшенная загрузка изображений

**Что меняется:**
- Добавить `import sys`
- Добавить `REFERENCE_WIDTH = 1280`, `REFERENCE_HEIGHT = 720`
- Добавить `SCALE_FACTOR = SCREEN_WIDTH / REFERENCE_WIDTH`
- Добавить `BLOCK_SIZE = 40` (только для ПК, без мобильной логики)
- Добавить функцию `find_image_file(path)` — регистронезависимый поиск файлов изображений
- Переработать `load_image()`:
  - Использовать `find_image_file()` для поиска
  - Для `.jpg` использовать `convert()`, для `.png` — `convert_alpha()`
  - Множественные fallback-пути для загрузки
  - Подробное логирование при ошибках загрузки
- **НЕ переносить:** `APP_PATH`, `android_log()`, `IS_MOBILE` расширенную логику, `MOBILE_*` константы

**Файл:** `pk_orig/setting.py`

### 2. game_platform.py — использование load_image() из setting

**Что меняется:**
- Заменить ручную загрузку `pygame.image.load(image_path).convert_alpha()` с тайлингом на вызов `load_image(image_path, width, height, color or GREEN)`
- Упростить код: убрать тайлинг, использовать централизованную функцию загрузки

**Файл:** `pk_orig/game_platform.py`

### 3. error_handler.py — использование find_image_file()

**Что меняется:**
- В методе `load_image_safe()` добавить использование `find_image_file()` из `setting` для регистронезависимого поиска
- Импортировать `from setting import find_image_file`

**Файл:** `pk_orig/error_handler.py`

### 4. menu.py — использование setting.SCREEN_WIDTH/HEIGHT

**Что меняется:**
- Добавить `import setting`
- Заменить `SCREEN_WIDTH` на `setting.SCREEN_WIDTH`
- Заменить `SCREEN_HEIGHT` на `setting.SCREEN_HEIGHT`

**Файл:** `pk_orig/menu.py`

### 5. level_select.py — использование setting.SCREEN_WIDTH/HEIGHT

**Что меняется:**
- Добавить `import setting`
- Заменить `SCREEN_WIDTH` на `setting.SCREEN_WIDTH`
- Заменить `SCREEN_HEIGHT` на `setting.SCREEN_HEIGHT`
- Для level_3 использовать `"levels/level_3.json"` вместо `f"levels/{level_id}.json"`

**Файл:** `pk_orig/level_select.py`

### 6. main.py — сохранение прогресса через save_manager

**Что меняется:**
- Добавить вызов `save_manager.update_level_progress(level_id, True, collected, total)` при завершении уровня (в блоке `if door_exit.level_complete:`)
- Вычислять `collected` и `total` перед вызовом
- Использовать `level_id` (уже есть в коде)

**Файл:** `pk_orig/main.py`

## Что НЕ переносится (мобильные части)

- `joystick.py` — целиком мобильный файл
- `IS_MOBILE` логика в `setting.py`
- `APP_PATH`, `android_log()` — только для Android
- Масштабирование в `levels.py` (scale factor для мобильных)
- Мобильное разрешение экрана в `main.py`
- `MOBILE_*` константы

## Порядок выполнения

1. `setting.py` — базовая инфраструктура (find_image_file, load_image)
2. `game_platform.py` — использует новую load_image
3. `error_handler.py` — использует find_image_file
4. `menu.py` — использует setting.SCREEN_WIDTH/HEIGHT
5. `level_select.py` — использует setting.SCREEN_WIDTH/HEIGHT
6. `main.py` — сохранение прогресса