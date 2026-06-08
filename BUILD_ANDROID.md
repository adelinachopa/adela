# Сборка APK для Android

## Требования

- **Linux** (Ubuntu 20.04/22.04 LTS рекомендуется) или **WSL2** на Windows
- **Python 3.8+**
- **Buildozer** — инструмент для сборки APK
- **Docker** (опционально, для упрощения сборки)

---

## Способ 1: Сборка через Docker (рекомендуемый)

Самый простой способ — использовать готовый Docker-образ с Buildozer.

### 1. Установка Docker

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install docker.io
sudo systemctl start docker
sudo usermod -aG docker $USER
# Выйдите и зайдите заново (или перезагрузите терминал)
```

### 2. Сборка APK

```bash
# Перейдите в корневую папку проекта
cd /path/to/escape-to-emk

# Запустите сборку через Docker
docker run --interactive --tty --rm \
    --volume "$(pwd)":/home/user/hostcwd \
    --volume ~/.buildozer:/home/user/.buildozer \
    kivy/buildozer -v android debug
```

После завершения сборки APK будет находиться в:
```
bin/escapetoemk-1.0-<arch>-debug.apk
```

---

## Способ 2: Сборка через Buildozer (нативная)

### 1. Установка зависимостей

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y \
    git zip unzip openjdk-17-jdk \
    python3-pip autoconf libtool \
    pkg-config zlib1g-dev libncurses5-dev \
    libncursesw5-dev libtinfo5 cmake \
    libffi-dev libssl-dev

# Установка Buildozer
pip3 install --user buildozer

# Добавьте ~/.local/bin в PATH
export PATH=$PATH:~/.local/bin
```

### 2. Инициализация Buildozer (если buildozer.spec отсутствует)

```bash
buildozer init
```

**Важно:** Если вы используете `buildozer init`, скопируйте настройки из существующего `buildozer.spec` в корне проекта.

### 3. Сборка APK

```bash
# Сборка debug-версии
buildozer -v android debug

# Сборка release-версии (требуется ключ подписи)
# buildozer -v android release
```

### 4. Где искать APK

После успешной сборки APK будет в папке `bin/`:
```
bin/escapetoemk-1.0-arm64-v8a-debug.apk
bin/escapetoemk-1.0-armeabi-v7a-debug.apk
```

---

## Установка на устройство

### Через ADB (Android Debug Bridge)

```bash
# Подключите устройство через USB (включите отладку по USB)
adb install bin/escapetoemk-1.0-arm64-v8a-debug.apk
```

### Вручную

1. Скопируйте APK на устройство
2. Откройте файловый менеджер
3. Нажмите на APK-файл
4. Подтвердите установку (разрешите установку из неизвестных источников)

---

## Тестирование и отладка

### Просмотр логов

```bash
adb logcat | grep -E "(python|pygame|SDL|Escape)"
```

### Запуск с отладкой

```bash
buildozer -v android debug deploy run
```

---

## Структура проекта для Android

```
escape-to-emk/
├── main.py              # Точка входа
├── setting.py           # Настройки
├── responsive.py        # Адаптивное масштабирование (НОВЫЙ)
├── joystick.py          # Мобильное управление
├── entities.py          # Игровые сущности
├── levels.py            # Логика уровней
├── level_loader.py      # Загрузчик уровней
├── level_select.py      # Выбор уровней
├── menu.py              # Меню
├── platform.py          # Платформы
├── save_manager.py      # Сохранения
├── error_handler.py     # Обработка ошибок
├── buildozer.spec       # Конфигурация сборки (НОВЫЙ)
├── requirements.txt     # Зависимости
├── levels/              # Файлы уровней (.json)
├── image/               # Изображения
│   ├── background/
│   ├── platform/
│   └── sprite/
└── plans/               # Документация
```

---

## Возможные проблемы

### 1. Ошибка "No module named 'pygame'"

Убедитесь, что в `buildozer.spec` в `requirements` указан `pygame`:
```ini
requirements = python3,pygame==2.5.2,sdl2
```

### 2. Ошибка "SDK not found"

Buildozer автоматически загружает SDK/NDK при первой сборке. Это может занять много времени (~2-3 ГБ).

### 3. Ошибка "Permission denied" при установке

На устройстве Android разрешите "Установка из неизвестных источников" в настройках безопасности.

### 4. Медленная сборка

Первая сборка может занять 20-40 минут (загрузка SDK, NDK, компиляция). Последующие сборки будут быстрее.

### 5. Проблемы с сенсорным вводом

Убедитесь, что в `main.py` используется `pygame.FULLSCREEN | pygame.SCALED` для корректной обработки сенсорных событий.

---

## Полезные ссылки

- [Buildozer Documentation](https://buildozer.readthedocs.io/)
- [Python-for-Android](https://python-for-android.readthedocs.io/)
- [Pygame on Android](https://pygame.org/wiki/Android)