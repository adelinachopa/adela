# План: Исправление PK.jpg и сборка APK

## Задача 1: PK.jpg парит визуально
**Статус:** Отложено.

## Задача 2: Сборка APK через WSL2
**Статус:** ✅ **APK собран!**

Файл: `escapetoemk-1.0.0-arm64-v8a_armeabi-v7a-debug.apk` (37.9 MB)

### Что было сделано

1. **Установлен WSL2 с Ubuntu** — `wsl -l -v` показывает Ubuntu Running
2. **Установлены зависимости** — `python3-pip`, `git`, `zip`, `unzip`, `openjdk-17-jdk`, `autoconf`, `libtool`, `pkg-config`, `zlib1g-dev`, `libncurses-dev`, `cmake`, `libffi-dev`, `libssl-dev`
3. **Установлен Buildozer** — через `pip3 install --user --break-system-packages buildozer`
4. **Создан `~/.config/pip/pip.conf`** с `break-system-packages = true` — чтобы Buildozer мог вызывать `pip install --user` внутри себя
5. **Установлен Python 3.11** через `deadsnakes` PPA — системный Python 3.14 несовместим с pygame 2.5.2
6. **Переключён `python3` на 3.11** через `update-alternatives`
7. **Пропатчены рецепты python-for-android** — изменена версия в `hostpython3/__init__.py` и `python3/__init__.py` с `3.14.2` на `3.11.0`
8. **Приняты лицензии Android SDK** — через `sdkmanager --licenses`
9. **Собран APK** — `buildozer -v android debug`

### Проблемы, которые возникли

| Проблема | Решение |
|----------|---------|
| `externally-managed-environment` (PEP 668) | `~/.config/pip/pip.conf` с `break-system-packages = true` |
| `platform.py` конфликт имён с stdlib | `cd ~ && pipx install cython` (из другой директории) |
| NTFS permissions на `/mnt/c/` | Копирование проекта в `~/emk_game/` |
| `hostpython3` скачивает 3.14.2 | Пропатчены рецепты p4a |
| pygame не компилируется с Python 3.14 | Установлен Python 3.11, пропатчены рецепты |
| Лицензии SDK не приняты | `yes | sdkmanager --licenses` |

### Команды для повторной сборки

```bash
# Войти в WSL
wsl -d Ubuntu -u user

# Перейти в проект
cd ~/emk_game

# Собрать APK
buildozer -v android debug
```

### Где лежит APK

- В WSL: `~/emk_game/bin/escapetoemk-1.0.0-arm64-v8a_armeabi-v7a-debug.apk`
- В Windows: `c:/Users/olego/OneDrive/Desktop/adela/escape to EMK/escapetoemk-1.0.0-arm64-v8a_armeabi-v7a-debug.apk`

## Диагностика: Аня не нажимает кнопки
**Статус:** Отложено.