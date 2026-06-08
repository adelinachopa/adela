#!/bin/bash
# Скрипт для копирования APK из WSL в Windows
# Запускать из WSL

APK_PATH="/home/user/emk_game/bin/escapetoemk-1.0.0-arm64-v8a_armeabi-v7a-debug.apk"
WINDOWS_DEST="/mnt/c/Users/olego/OneDrive/Desktop/adela/escape to EMK/bin/"

if [ -f "$APK_PATH" ]; then
    echo "Copying APK to Windows..."
    cp "$APK_PATH" "$WINDOWS_DEST"
    echo "Done! APK copied to: $WINDOWS_DEST"
    ls -la "${WINDOWS_DEST}escapetoemk"*.apk
else
    echo "ERROR: APK not found at $APK_PATH"
    echo "Build may still be in progress or may have failed."
    exit 1
fi