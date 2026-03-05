[app]
title = King App
package.name = kingapp
package.domain = com.kingai
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,txt
version = 1.0

# Strictly defined requirements for stability
requirements = python3,kivy==2.3.0,plyer,pyjnius==1.4.2,kivmob

orientation = portrait

# Added ACCESS_NETWORK_STATE (Required for AdMob to check connection)
android.permissions = INTERNET, ACCESS_NETWORK_STATE

# Updated to Android 14 (API 34) standards for Google Play compliance
android.minapi = 24
android.api = 34
android.ndk = 25b
android.build_tools_version = 34.0.0

android.accept_sdk_license = True
android.presplash_color = #1a1a2e

# YOUR REAL ADMOB APP ID (From your latest screenshot)
android.meta_data = com.google.android.gms.ads.APPLICATION_ID=ca-app-pub-9057426786910647~6778392532

[buildozer]
log_level = 2
warn_on_root = 1
