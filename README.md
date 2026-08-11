# 🎵 MusicHub — Online + Local Audio Player & Android Mobile App

MusicHub is a modern, high-performance, eye-care audio player for Desktop (Windows/Linux/macOS) and Android mobile devices.

---

## ✨ Features

- **Online Stream Engine**: Search and stream over 100M+ songs via iTunes Search API with guaranteed 256kbps audio feeds.
- **Local Audio Library**: Scan local folders for `.mp3`, `.flac`, `.wav`, `.m4a`, and `.ogg` files.
- **Spinning Vinyl Graphic**: High-definition vinyl disc animation (`1200x1200`) with circular album artwork label.
- **Interactive Preset Themes**:
  - 🌸 **Soft Coral Peach** (Eye-Care warm charcoal slate with soft coral accents)
  - 💚 **Emerald Green** (Spotify-style soothing green music aesthetic)
  - 💜 **Cyberpunk Neon** (High-energy purple & cyan dark mode)
  - 💙 **Electric Cyan** (High-contrast deep navy slate with cyan accents)
- **Full Playback Controls**: Progress slider with seek support, volume slider with mute toggle, shuffle (`🔀`), repeat (`🔁 ALL` / `🔂 ONE`), and animated visualizer (` ▂▃▅▇ `).
- **Android Support**: Mobile-ready Kivy application ([`main_kivy.py`](file:///main_kivy.py)) and Buildozer configuration ([`buildozer.spec`](file:///buildozer.spec)) for compiling `.apk` installers.

---

## 🚀 Desktop Installation & Run

1. **Clone Repository**:
   ```bash
   git clone https://github.com/SyndicateAkshat/MusicHub.git
   cd MusicHub
   ```

2. **Install Dependencies**:
   ```bash
   pip install customtkinter pillow requests python-vlc
   ```

3. **Run Application**:
   ```bash
   python main.py
   ```

---

## 📱 Android APK Compilation

### Option A: Google Colab (1-Click Free Cloud Build)
1. Upload [`Build_MusicHub_Android_APK.ipynb`](file:///Build_MusicHub_Android_APK.ipynb) to [Google Colab](https://colab.research.google.com/).
2. Run all cells. The APK file (`MusicHub-1.0.0-debug.apk`) will compile and download to your device in ~5 minutes!

### Option B: Local Linux / WSL Build
```bash
bash build_apk.sh
```

---

## 📜 License
MIT License. Free for open-source use.
