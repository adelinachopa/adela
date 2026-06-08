[app]

# (str) Title of your application
title = Escape to EMK

# (str) Package name
package.name = escapetoemk

# (str) Package domain (needed for android/ios packaging)
package.domain = org.emk

# (str) Version of the application
version = 1.0.0

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (patterns)
source.include_exts = py,png,jpg,jpeg,gif,json,txt

# (list) List of inclusions using pattern matching
source.include_patterns = *.py, levels/*.json, image/**/*.png, image/**/*.jpg, image/**/*.jpeg

# (list) Source files to exclude (patterns)
# source.exclude_exts = spec

# (list) List of directory to exclude (patterns)
# source.exclude_dirs = tests, bin

# (list) List of additional requirements to install
requirements = python3==3.11.0,cython==0.29.33,pygame==2.1.3,sdl2

# (str) Presplash of the application
# presplash.filename = %(source.dir)s/data/splash.png

# (str) Icon of the application
# icon.filename = %(source.dir)s/data/icon.png

# (str) Supported orientation (one of landscape, sensorLandscape, portrait or all)
orientation = landscape

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 1

# (list) Permissions
android.permissions = INTERNET

# (int) Android API to use
android.api = 31

# (int) Minimum API required
android.minapi = 21

# (int) Android SDK version to use
# android.sdk = 24

# (str) Android NDK version to use
# android.ndk = 23b

# (bool) Use Android's private storage for application data
android.private_storage = True

# (str) Android logcat filter to use
# android.logcat_filters = *:S

# (bool) Copy library instead of making a libsymlink
# android.copy_libs = 1

# (str) The Android arch to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
android.archs = arm64-v8a, armeabi-v7a

# (int) When Android is set to fullscreen, leave the top status bar hidden
android.wakelock = True

# (str) Window size in portrait mode
# android.window_size = 800x480

# (str) Supported Android TV features
# android.tv_features = android.hardware.touchscreen

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug)
log_level = 2

# (int) Number of parallel jobs to use during build
# jobs = 4

# (str) Where to store the log file
log_filename = buildozer.log

# (str) Global requirements (will be installed in the build environment)
# global_requirements = setuptools

[warn]

# (list) List of warnings to ignore
# ignore = I686SUPPORT

# (str) Path to the Android SDK
# android.sdk_path = /home/user/android-sdk

# (str) Path to the Android NDK
# android.ndk_path = /home/user/android-ndk

# (str) Path to the Android ANT
# android.ant_path = /home/user/apache-ant