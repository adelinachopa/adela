#!/bin/bash
readelf -s /home/user/emk_game/.buildozer/android/platform/build-arm64-v8a_armeabi-v7a/dists/escapetoemk/_python_bundle__arm64-v8a/_python_bundle/site-packages/pygame/surface.so 2>/dev/null | grep UND | grep -i sse2
echo "---"
readelf -s /home/user/emk_game/.buildozer/android/platform/build-arm64-v8a_armeabi-v7a/dists/escapetoemk/_python_bundle__arm64-v8a/_python_bundle/site-packages/pygame/surface.so 2>/dev/null | grep UND | grep -i blit