[app]

# (str) Title of your application
title = MusicHub

# (str) Package name
package.name = musichub

# (str) Package domain (needed for android/ios packaging)
package.domain = org.musichub

# (str) Source code where the main.py lives
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas

# (str) Application versioning (method 1)
version = 1.0.0

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
requirements = python3,kivy,requests,urllib3,chardet,idna,certifi

# (str) Custom source folders for requirements
# Sets custom source for any requirement with recipes or site-packages
# requirements.source.kivy = ../kivy

# (list) Garden requirements
#garden_requirements =

# (str) Presets useful to setup default values for buildozer
# target = android

# (str) Icon of the application
# icon.filename = %(source.dir)s/data/icon.png

# (str) Supported orientation (one of landscape, sensorLandscape, portrait or all)
orientation = portrait

# (list) List of service to declare
#services =

#
# Android specific
#

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (string) Preserved Android logcat filters
#android.logcat_filters = *:S python:D

# (list) Android permissions
android.permissions = INTERNET, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, READ_MEDIA_AUDIO

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK will support.
android.minapi = 21

# (str) Android NDK version to use
#android.ndk = 25b

# (bool) Use --private data storage (True) or --dir public storage (False)
#android.private_storage = True

# (str) Android NDK directory (if empty, it will be automatically downloaded.)
#android.ndk_path =

# (str) Android SDK directory (if empty, it will be automatically downloaded.)
#android.sdk_path =

# (str) ANT directory (if empty, it will be automatically downloaded.)
#android.ant_path =

# (list) Android application options
android.archs = arm64-v8a, armeabi-v7a

# (bool) Enable AndroidX support. Required when targeting API 29+
android.enable_androidx = True

# (bool) Enable User Environment
android.accept_sdk_license = True

#
# Buildozer section
#

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = disable, 1 = enable)
warn_on_root = 1
