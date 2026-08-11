#!/bin/bash
# Script to compile MusicHub into an Android APK using Buildozer

echo "=== 1. Installing Buildozer & Android Build Dependencies ==="
sudo apt-get update
sudo apt-get install -y build-essential git python3-pip ccache libffi-dev libssl-dev libxml2-dev libxslt1-dev zlib1g-dev openjdk-17-jdk unzip zip

pip install --upgrade buildozer cython kivy

echo "=== 2. Building Android APK ==="
buildozer -v android debug

echo "=== 3. Build Completed! ==="
echo "Your APK file is located in the bin/ directory:"
ls -lh bin/*.apk
