[app]

title = King App
package.name = kingapp
package.domain = com.kingai
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,txt
version = 1.0

# FIX: pyjnius pinned to 1.4.2 — latest version breaks with Python 3 (uses removed 'long' type)
requirements = python3,kivy==2.3.0,plyer,pyjnius==1.4.2

orientation = portrait
android.permissions = INTERNET
android.minapi = 21
android.api = 33
android.ndk = 25b
android.build_tools_version = 33.0.0
android.accept_sdk_license = True
android.presplash_color = #1a1a2e

[buildozer]
build_dir = .buildozer
bin_dir = ./bin
log_level = 2
warn_on_root = 1
