[app]

# App title — shown on home screen
title = King App

# Package name — must be unique (use your domain reversed)
package.name = kingapp

# Package domain
package.domain = com.kingai

# Source directory (where main.py is)
source.dir = .

# Source files to include
source.include_exts = py,png,jpg,kv,atlas,json,txt

# App version
version = 1.0

# Requirements — add any extra Python libs here
requirements = python3,kivy==2.3.0,psutil,plyer

# App orientation
orientation = portrait

# Android permissions
android.permissions = INTERNET

# Minimum Android version (API 21 = Android 5.0)
android.minapi = 21

# Target Android version
android.api = 33

# NDK version
android.ndk = 25b

# SDK build tools version
android.build_tools_version = 33.0.0

# Accept Android SDK licenses automatically
android.accept_sdk_license = True

# Entry point
entrypoint = main.py

# App icon (place a 512x512 PNG named icon.png in your project root)
# icon.filename = %(source.dir)s/assets/icon.png

# Splash screen
# presplash.filename = %(source.dir)s/assets/splashscreen.png

# Presplash background color
android.presplash_color = #1a1a2e

# Debug or release
# android.release_artifact = aab

[buildozer]

# Build directory
build_dir = .buildozer

# Bin directory (where APK goes)
bin_dir = ./bin

# Logging level (0=error, 1=info, 2=debug)
log_level = 2

# Warn on errors
warn_on_root = 1
