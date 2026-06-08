#!/bin/bash
export PATH=/home/user/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
cd /home/user/emk_game
rm -rf .buildozer/android/platform/build-arm64-v8a_armeabi-v7a/build/other_builds/pygame
rm -rf .buildozer/android/platform/build-arm64-v8a_armeabi-v7a/dists/escapetoemk
buildozer android debug > /tmp/buildozer_output3.log 2>&1 &
echo BUILD_PID=$!