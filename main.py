import html
import io
import os
import random
import threading
from tkinter import filedialog

import customtkinter as ctk
import requests
from PIL import Image, ImageDraw

from services.audio_service import AudioPlayer
from services.jiosaavn_api import search_songs

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DISK_IMAGE_PATH = os.path.join(APP_DIR, "assets", "disk.png")
LOCAL_AUDIO_EXTENSIONS = (".mp3", ".wav", ".flac", ".m4a", ".ogg", ".aac", ".wma")

# Preset Theme Definitions
THEMES = {
    "🌸 Soft Coral Peach": {
        "mode": "dark", "bg": "#121721", "panel": "#1A222F", "card": "#232D3F",
        "primary": "#FF7675", "secondary": "#FF6B6B", "hover": "#E84393",
        "text": "#E6EDF3", "muted": "#8B949E", "row_hl": "#36262B",
        "ring1": (255, 118, 117, 220), "ring2": (255, 107, 107, 180)
    },
    "💚 Emerald Green": {
        "mode": "dark", "bg": "#121721", "panel": "#1A222F", "card": "#232D3F",
        "primary": "#2ECC71", "secondary": "#10B981", "hover": "#27AE60",
        "text": "#E6EDF3", "muted": "#8B949E", "row_hl": "#1E3A2B",
        "ring1": (46, 204, 113, 220), "ring2": (16, 185, 129, 180)
    },
    "💜 Cyberpunk Neon": {
        "mode": "dark", "bg": "#0B0C10", "panel": "#141622", "card": "#1E2132",
        "primary": "#6C5CE7", "secondary": "#00CEC9", "hover": "#5B4BC4",
        "text": "#FFFFFF", "muted": "#9EA4C1", "row_hl": "#272A42",
        "ring1": (108, 92, 231, 220), "ring2": (0, 206, 201, 180)
    },
    "💙 Electric Cyan": {
        "mode": "dark", "bg": "#0F172A", "panel": "#1E293B", "card": "#334155",
        "primary": "#00CEC9", "secondary": "#38BDF8", "hover": "#0891B2",
        "text": "#F8FAFC", "muted": "#94A3B8", "row_hl": "#164E63",
        "ring1": (0, 206, 201, 220), "ring2": (56, 189, 248, 180)
    }
}


current_theme_name = "🌸 Soft Coral Peach"
current_theme = THEMES[current_theme_name]

ctk.set_appearance_mode(current_theme["mode"])
ctk.set_default_color_theme("blue")

app = ctk.CTk(fg_color=current_theme["bg"])
app.title("MusicHub — Online + Local Audio Player")
app.geometry("1060x740")
app.minsize(960, 660)

audio_player = AudioPlayer()

# State
online_playlist: list[dict] = []
local_playlist: list[dict] = []
current_playlist: list[dict] = []
active_source: str = "online"
current_index: int = 0
is_playing: bool = False
is_seeking: bool = False
is_shuffle: bool = False
repeat_mode: str = "off"
rotation_angle: int = 0
rotate_timer = None
eq_frame_idx: int = 0
cached_art_img: Image.Image = None

DISC_SIZE, ART_SIZE = 240, 110
disk_base_image = Image.open(DISK_IMAGE_PATH).convert("RGBA").resize((DISC_SIZE, DISC_SIZE), Image.Resampling.LANCZOS)
current_disc_pil: Image.Image = disk_base_image.copy()
album_art_cache: dict[str, Image.Image] = {}

online_row_widgets: list[ctk.CTkButton] = []
local_row_widgets: list[ctk.CTkButton] = []

EQ_FRAMES = [" ▂▃▅▇▅▃ ", " ▃▅▇▅▃▂ ", " ▅▇▅▃▂  ", " ▇▅▃▂ ▃ ", " ▅▃▂ ▃▅ ", " ▃▂ ▃▅▇ "]


def build_composite_disc(art_img: Image.Image = None) -> Image.Image:
    """Build vinyl disc image using current theme glow rings and circular album art."""
    disc_canvas = disk_base_image.copy()
    overlay = Image.new("RGBA", (DISC_SIZE, DISC_SIZE), (0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(overlay)
    draw_overlay.ellipse((2, 2, DISC_SIZE - 2, DISC_SIZE - 2), outline=current_theme["ring1"], width=3)
    draw_overlay.ellipse((6, 6, DISC_SIZE - 6, DISC_SIZE - 6), outline=current_theme["ring2"], width=2)
    disc_canvas = Image.alpha_composite(disc_canvas, overlay)

    if art_img is not None:
        art_resized = art_img.convert("RGBA").resize((ART_SIZE, ART_SIZE), Image.Resampling.LANCZOS)
        mask = Image.new("L", (ART_SIZE, ART_SIZE), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, ART_SIZE, ART_SIZE), fill=255)
        pos = ((DISC_SIZE - ART_SIZE) // 2, (DISC_SIZE - ART_SIZE) // 2)
        disc_canvas.paste(art_resized, pos, mask)

        draw_disc = ImageDraw.Draw(disc_canvas)
        draw_disc.ellipse((pos[0], pos[1], pos[0] + ART_SIZE, pos[1] + ART_SIZE), outline=current_theme["ring2"], width=2)
        cx, cy, hole_r = DISC_SIZE // 2, DISC_SIZE // 2, 10
        draw_disc.ellipse((cx - hole_r - 2, cy - hole_r - 2, cx + hole_r + 2, cy + hole_r + 2), fill=(75, 60, 65, 255))
        draw_disc.ellipse((cx - hole_r, cy - hole_r, cx + hole_r, cy + hole_r), fill=(22, 18, 20, 255))

    return disc_canvas


def format_time(ms: int) -> str:
    s = max(0, ms // 1000)
    return f"{s // 60:02d}:{s % 60:02d}"


current_disc_pil = build_composite_disc(None)

# Layout
main_frame = ctk.CTkFrame(app, fg_color="transparent")
main_frame.pack(fill="both", expand=True, padx=16, pady=16)

left_panel = ctk.CTkFrame(main_frame, width=420, fg_color=current_theme["panel"], corner_radius=16)
left_panel.pack(side="left", fill="y", padx=(0, 16))
left_panel.pack_propagate(False)

right_panel = ctk.CTkFrame(main_frame, fg_color=current_theme["panel"], corner_radius=16)
right_panel.pack(side="left", fill="both", expand=True)

# Header Bar with Brand Title & Interactive Theme Picker Dropdown
brand_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
brand_frame.pack(fill="x", padx=15, pady=(15, 5))

brand_title = ctk.CTkLabel(brand_frame, text="🎵 MusicHub", font=("Segoe UI", 18, "bold"), text_color=current_theme["secondary"])
brand_title.pack(side="left")

theme_menu = ctk.CTkOptionMenu(
    brand_frame,
    values=list(THEMES.keys()),
    width=140,
    height=28,
    font=("Segoe UI", 11, "bold"),
    dropdown_font=("Segoe UI", 11),
    fg_color=current_theme["primary"],
    button_color=current_theme["primary"],
    button_hover_color=current_theme["hover"],
    text_color="#FFFFFF",
    dropdown_fg_color=current_theme["card"],
    dropdown_hover_color=current_theme["hover"],
    dropdown_text_color=current_theme["text"],
    command=lambda name: change_theme(name)
)
theme_menu.set(current_theme_name)
theme_menu.pack(side="right")

# Source Tabs
tabview = ctk.CTkTabview(
    left_panel, fg_color=current_theme["card"],
    segmented_button_selected_color=current_theme["primary"],
    segmented_button_selected_hover_color=current_theme["hover"],
    segmented_button_unselected_color="#1A222F",
    segmented_button_unselected_hover_color="#2A374A",
    text_color=current_theme["text"],
)
tabview.pack(fill="both", expand=True, padx=12, pady=(5, 0))
online_tab, local_tab = tabview.add("Online Search"), tabview.add("Local Files")

status_label = ctk.CTkLabel(left_panel, text="✨ Select a song to start listening", text_color=current_theme["muted"], font=("Segoe UI", 12))
status_label.pack(pady=10)

# Online Tab
search_row = ctk.CTkFrame(online_tab, fg_color="transparent")
search_row.pack(fill="x", pady=(5, 8))

search_entry = ctk.CTkEntry(
    search_row, placeholder_text="🔍 Search songs, artists, albums…", font=("Segoe UI", 13),
    fg_color="#18202C", border_color="#2A374A", border_width=1, text_color=current_theme["text"], corner_radius=10, height=38,
)

search_entry.pack(side="left", fill="x", expand=True)

search_btn = ctk.CTkButton(
    search_row, text="Search", font=("Segoe UI", 12, "bold"), fg_color=current_theme["primary"],
    hover_color=current_theme["hover"], text_color="#FFFFFF", corner_radius=10, width=75, height=38,
    command=lambda: on_search(),
)
search_btn.pack(side="left", padx=(8, 0))

online_results_frame = ctk.CTkScrollableFrame(online_tab, label_text="Trending & Search Results", label_fg_color=current_theme["card"], label_text_color=current_theme["secondary"], fg_color="transparent")
online_results_frame.pack(fill="both", expand=True, pady=(0, 5))

# Local Tab
local_folder_row = ctk.CTkFrame(local_tab, fg_color="transparent")
local_folder_row.pack(fill="x", pady=(5, 8))

choose_folder_btn = ctk.CTkButton(
    local_folder_row, text="📁 Select Music Folder…", font=("Segoe UI", 13, "bold"),
    fg_color=current_theme["primary"], hover_color=current_theme["hover"], text_color="#FFFFFF", corner_radius=10, height=38,
    command=lambda: choose_local_folder(),
)
choose_folder_btn.pack(side="left", fill="x", expand=True)

local_folder_label = ctk.CTkLabel(local_tab, text="No folder selected", text_color=current_theme["muted"], anchor="w", font=("Segoe UI", 11))
local_folder_label.pack(fill="x", pady=(0, 5))

local_results_frame = ctk.CTkScrollableFrame(local_tab, label_text="Local Audio Files", label_fg_color=current_theme["card"], label_text_color=current_theme["secondary"], fg_color="transparent")
local_results_frame.pack(fill="both", expand=True, pady=(0, 5))

# Right Panel: Player View
top_badge_row = ctk.CTkFrame(right_panel, fg_color="transparent")
top_badge_row.pack(fill="x", padx=25, pady=(20, 5))

source_badge = ctk.CTkLabel(top_badge_row, text="🎧 ONLINE STREAM", font=("Segoe UI", 10, "bold"), fg_color=current_theme["card"], text_color=current_theme["secondary"], corner_radius=6, padx=8, pady=3)
source_badge.pack(side="left")

eq_visualizer_label = ctk.CTkLabel(top_badge_row, text=" ▂▃▅▇ ", font=("Consolas", 12, "bold"), text_color=current_theme["primary"])
eq_visualizer_label.pack(side="right")

title_label = ctk.CTkLabel(right_panel, text="No Track Selected", font=("Segoe UI", 22, "bold"), text_color=current_theme["text"], wraplength=480)
title_label.pack(pady=(10, 2))

artist_label = ctk.CTkLabel(right_panel, text="Search online or select local music to start listening", font=("Segoe UI", 13), text_color=current_theme["muted"], wraplength=480)
artist_label.pack(pady=(0, 10))

art_container = ctk.CTkFrame(right_panel, fg_color="transparent", width=DISC_SIZE, height=DISC_SIZE)
art_container.pack(pady=10)

initial_ctk_disc = ctk.CTkImage(light_image=current_disc_pil, dark_image=current_disc_pil, size=(DISC_SIZE, DISC_SIZE))
disk_label = ctk.CTkLabel(art_container, text="", image=initial_ctk_disc)
disk_label.place(relx=0.5, rely=0.5, anchor="center")

# Progress Card
progress_card = ctk.CTkFrame(right_panel, fg_color=current_theme["card"], corner_radius=12)
progress_card.pack(fill="x", padx=25, pady=(15, 10))

time_current_label = ctk.CTkLabel(progress_card, text="00:00", font=("Consolas", 12, "bold"), text_color=current_theme["secondary"])
time_current_label.pack(side="left", padx=(15, 10), pady=10)

seek_slider = ctk.CTkSlider(
    progress_card, from_=0, to=1000, number_of_steps=1000,
    button_color=current_theme["secondary"], button_hover_color=current_theme["primary"], progress_color=current_theme["primary"],
    fg_color="#2E3B4E" if current_theme["mode"] == "dark" else "#CBD5E1", height=16,
)
seek_slider.set(0)
seek_slider.pack(side="left", fill="x", expand=True, pady=10)

time_total_label = ctk.CTkLabel(progress_card, text="00:00", font=("Consolas", 12, "bold"), text_color=current_theme["muted"])
time_total_label.pack(side="right", padx=(10, 15), pady=10)

# Controls
controls_row = ctk.CTkFrame(right_panel, fg_color="transparent")
controls_row.pack(pady=10)

shuffle_btn = ctk.CTkButton(controls_row, text="🔀", width=45, height=40, font=("Segoe UI", 14), fg_color=current_theme["card"], hover_color=current_theme["hover"], text_color=current_theme["text"], corner_radius=10, command=lambda: toggle_shuffle())
shuffle_btn.grid(row=0, column=0, padx=8)

prev_btn = ctk.CTkButton(controls_row, text="⏮", width=55, height=40, font=("Segoe UI", 16), fg_color=current_theme["card"], hover_color=current_theme["hover"], text_color=current_theme["text"], corner_radius=10, command=lambda: previous_song())
prev_btn.grid(row=0, column=1, padx=8)

play_pause_btn = ctk.CTkButton(controls_row, text="▶ PLAY", width=110, height=44, font=("Segoe UI", 14, "bold"), fg_color=current_theme["primary"], hover_color=current_theme["hover"], text_color="#FFFFFF", corner_radius=12, command=lambda: toggle_play_pause())
play_pause_btn.grid(row=0, column=2, padx=10)

stop_btn = ctk.CTkButton(controls_row, text="⏹", width=55, height=40, font=("Segoe UI", 16), fg_color=current_theme["primary"], hover_color="#C0392B", text_color="#FFFFFF", corner_radius=10, command=lambda: stop())
stop_btn.grid(row=0, column=3, padx=8)

next_btn = ctk.CTkButton(controls_row, text="⏭", width=55, height=40, font=("Segoe UI", 16), fg_color=current_theme["card"], hover_color=current_theme["hover"], text_color=current_theme["text"], corner_radius=10, command=lambda: next_song())
next_btn.grid(row=0, column=4, padx=8)

repeat_btn = ctk.CTkButton(controls_row, text="🔁", width=45, height=40, font=("Segoe UI", 14), fg_color=current_theme["card"], hover_color=current_theme["hover"], text_color=current_theme["text"], corner_radius=10, command=lambda: toggle_repeat())
repeat_btn.grid(row=0, column=5, padx=8)

# Volume
volume_row = ctk.CTkFrame(right_panel, fg_color="transparent")
volume_row.pack(pady=(5, 15))

volume_icon_btn = ctk.CTkButton(volume_row, text="🔊", width=35, fg_color="transparent", hover=False, font=("Segoe UI", 14), text_color=current_theme["text"], command=lambda: toggle_mute())
volume_icon_btn.pack(side="left", padx=(0, 6))

volume_slider = ctk.CTkSlider(
    volume_row, from_=0, to=100, width=160, number_of_steps=100,
    button_color=current_theme["primary"], button_hover_color=current_theme["secondary"], progress_color=current_theme["secondary"],
    fg_color="#2E3B4E" if current_theme["mode"] == "dark" else "#CBD5E1",
)
volume_slider.set(80)
volume_slider.pack(side="left")

vol_value_label = ctk.CTkLabel(volume_row, text="80%", font=("Consolas", 11, "bold"), text_color=current_theme["muted"], width=40)
vol_value_label.pack(side="left", padx=(6, 0))
saved_volume = 80

# Seeking & Volume Callbacks
seek_slider.bind("<ButtonPress-1>", lambda e: globals().update(is_seeking=True))
seek_slider.bind("<ButtonRelease-1>", lambda e: (audio_player.set_position(seek_slider.get() / 1000.0) if audio_player.is_loaded() else None, globals().update(is_seeking=False)))


# ---------------- DYNAMIC THEME SWITCHER ----------------

def change_theme(name: str):
    global current_theme_name, current_theme, current_disc_pil
    if name not in THEMES:
        return
    current_theme_name = name
    current_theme = THEMES[name]

    ctk.set_appearance_mode(current_theme["mode"])

    # Update Backgrounds & Panels
    app.configure(fg_color=current_theme["bg"])
    left_panel.configure(fg_color=current_theme["panel"])
    right_panel.configure(fg_color=current_theme["panel"])

    brand_title.configure(text_color=current_theme["secondary"])
    theme_menu.configure(
        fg_color=current_theme["primary"], button_color=current_theme["primary"], button_hover_color=current_theme["hover"],
        dropdown_fg_color=current_theme["card"], dropdown_hover_color=current_theme["hover"], dropdown_text_color=current_theme["text"]
    )

    tabview.configure(
        fg_color=current_theme["card"], segmented_button_selected_color=current_theme["primary"],
        segmented_button_selected_hover_color=current_theme["hover"], text_color=current_theme["text"]
    )

    status_label.configure(text_color=current_theme["muted"])
    search_entry.configure(
        fg_color="#18202C" if current_theme["mode"] == "dark" else "#FFFFFF",
        border_color="#2A374A" if current_theme["mode"] == "dark" else "#FFC2D1", text_color=current_theme["text"]
    )
    search_btn.configure(fg_color=current_theme["primary"], hover_color=current_theme["hover"])
    online_results_frame.configure(label_fg_color=current_theme["card"], label_text_color=current_theme["secondary"])

    choose_folder_btn.configure(fg_color=current_theme["primary"], hover_color=current_theme["hover"])
    local_folder_label.configure(text_color=current_theme["muted"])
    local_results_frame.configure(label_fg_color=current_theme["card"], label_text_color=current_theme["secondary"])

    source_badge.configure(fg_color=current_theme["card"], text_color=current_theme["secondary"])
    eq_visualizer_label.configure(text_color=current_theme["primary"])
    title_label.configure(text_color=current_theme["text"])
    artist_label.configure(text_color=current_theme["muted"])

    progress_card.configure(fg_color=current_theme["card"])
    time_current_label.configure(text_color=current_theme["secondary"])
    seek_slider.configure(
        button_color=current_theme["secondary"], button_hover_color=current_theme["primary"], progress_color=current_theme["primary"],
        fg_color="#2E3B4E" if current_theme["mode"] == "dark" else "#CBD5E1"
    )
    time_total_label.configure(text_color=current_theme["muted"])

    shuffle_btn.configure(fg_color=current_theme["primary"] if is_shuffle else current_theme["card"], text_color=current_theme["text"])
    prev_btn.configure(fg_color=current_theme["card"], text_color=current_theme["text"])
    play_pause_btn.configure(fg_color=current_theme["primary"])
    next_btn.configure(fg_color=current_theme["card"], text_color=current_theme["text"])
    repeat_btn.configure(fg_color=current_theme["primary"] if repeat_mode != "off" else current_theme["card"], text_color=current_theme["text"])

    volume_icon_btn.configure(text_color=current_theme["text"])
    volume_slider.configure(
        button_color=current_theme["primary"], button_hover_color=current_theme["secondary"], progress_color=current_theme["secondary"],
        fg_color="#2E3B4E" if current_theme["mode"] == "dark" else "#CBD5E1"
    )
    vol_value_label.configure(text_color=current_theme["muted"])

    # Rebuild Vinyl Disc with new theme glow rings
    current_disc_pil = build_composite_disc(cached_art_img)
    _update_disc_label(current_disc_pil)

    # Refresh row highlights
    _update_playlist_highlights()


def on_volume_change(val):
    global saved_volume
    vol = int(val)
    audio_player.set_volume(vol)
    vol_value_label.configure(text=f"{vol}%")
    volume_icon_btn.configure(text="🔇" if vol == 0 else "🔉" if vol < 50 else "🔊")
    if vol > 0: saved_volume = vol


def toggle_mute():
    cur = audio_player.get_volume()
    v = 0 if cur > 0 else (saved_volume if saved_volume > 0 else 80)
    volume_slider.set(v)
    on_volume_change(v)


volume_slider.configure(command=on_volume_change)


def toggle_shuffle():
    global is_shuffle
    is_shuffle = not is_shuffle
    shuffle_btn.configure(fg_color=current_theme["primary"] if is_shuffle else current_theme["card"], text="🔀 ON" if is_shuffle else "🔀")


def toggle_repeat():
    global repeat_mode
    repeat_mode = "all" if repeat_mode == "off" else ("one" if repeat_mode == "all" else "off")
    lbl = "🔁 ALL" if repeat_mode == "all" else ("🔂 ONE" if repeat_mode == "one" else "🔁")
    repeat_btn.configure(fg_color=current_theme["primary"] if repeat_mode != "off" else current_theme["card"], text=lbl)


# Results & Highlights
def _populate_results(songs: list[dict], frame: ctk.CTkScrollableFrame, source: str, empty_msg: str, found_msg: str):
    global online_playlist, local_playlist, online_row_widgets, local_row_widgets
    if source == "online":
        online_playlist, row_widgets = songs, online_row_widgets
    else:
        local_playlist, row_widgets = songs, local_row_widgets

    row_widgets.clear()
    for w in frame.winfo_children(): w.destroy()

    if not songs:
        status_label.configure(text=f"⚠️ {empty_msg}")
        return

    status_label.configure(text=f"✨ {found_msg.format(n=len(songs))}")
    for i, song in enumerate(songs):
        row = ctk.CTkButton(
            frame, text=f"{i+1:02d}.  {song['title']}\n       {song['artist']}", anchor="w",
            fg_color="transparent", hover_color=current_theme["hover"], font=("Segoe UI", 12), text_color=current_theme["text"], corner_radius=8, height=44,
            command=lambda src=source, idx=i: play_song_from_source(src, idx),
        )
        row.pack(fill="x", pady=2)
        row_widgets.append(row)
    _update_playlist_highlights()


def _update_playlist_highlights():
    for i, btn in enumerate(online_row_widgets):
        active = (active_source == "online" and i == current_index and is_playing)
        btn.configure(fg_color=current_theme["row_hl"] if active else "transparent", text_color=current_theme["secondary"] if active else current_theme["text"])
    for i, btn in enumerate(local_row_widgets):
        active = (active_source == "local" and i == current_index and is_playing)
        btn.configure(fg_color=current_theme["row_hl"] if active else "transparent", text_color=current_theme["secondary"] if active else current_theme["text"])


# Online Search
def on_search(event=None):
    q = search_entry.get().strip()
    if not q: return
    status_label.configure(text="🔍 Searching online music catalog…")
    threading.Thread(target=lambda: _search_worker(q), daemon=True).start()


def _search_worker(q: str):
    try: songs = search_songs(q, limit=25)
    except Exception as e:
        app.after(0, lambda: status_label.configure(text=f"❌ Connection error: {e}"))
        return
    app.after(0, lambda: _populate_results(songs, online_results_frame, "online", "No songs found for search query", "{n} tracks loaded ready to play"))


search_entry.bind("<Return>", on_search)


# Local Folder Scan
def choose_local_folder():
    folder = filedialog.askdirectory(title="Select a folder with audio files")
    if not folder: return
    local_folder_label.configure(text=f"📁 {folder}")
    status_label.configure(text="Scanning folder for audio tracks…")
    threading.Thread(target=lambda: _scan_local_worker(folder), daemon=True).start()


def _scan_local_worker(folder: str):
    songs = []
    try:
        for fname in sorted(os.listdir(folder)):
            if fname.lower().endswith(LOCAL_AUDIO_EXTENSIONS):
                p = os.path.join(folder, fname)
                songs.append({"id": p, "title": html.unescape(os.path.splitext(fname)[0]), "artist": "Local Audio File", "album": os.path.basename(folder), "image_url": None, "stream_url": p, "duration": None})
    except OSError as e:
        app.after(0, lambda: status_label.configure(text=f"❌ Error reading folder: {e}"))
        return
    app.after(0, lambda: _populate_results(songs, local_results_frame, "local", "No supported audio files in folder", "{n} local audio files loaded"))


# Playback Logic
def play_song_from_source(source: str, idx: int):
    global current_playlist, active_source, current_index
    active_source, current_index = source, idx
    current_playlist = online_playlist if source == "online" else local_playlist
    source_badge.configure(text="⚡ ONLINE STREAM" if source == "online" else "📁 LOCAL AUDIO FILE", text_color=current_theme["secondary"] if source == "online" else current_theme["primary"])
    _load_and_play()


def _load_and_play():
    global current_disc_pil, cached_art_img
    if not current_playlist or not (0 <= current_index < len(current_playlist)): return
    song = current_playlist[current_index]
    title_label.configure(text=song["title"])
    artist_label.configure(text=f"🎵 {song['artist']}" + (f" • {song['album']}" if song.get('album') else ""))
    status_label.configure(text="⏳ Loading audio stream…")
    cached_art_img = None
    current_disc_pil = build_composite_disc(None)
    _update_disc_label(current_disc_pil)
    threading.Thread(target=lambda: _play_worker(song), daemon=True).start()


def _play_worker(song: dict):
    try:
        audio_player.load(song["stream_url"])
        audio_player.play()
    except Exception as e:
        app.after(0, lambda: status_label.configure(text=f"❌ Playback error: {e}"))
        return
    app.after(0, lambda: _on_play_started(song))


def _on_play_started(song: dict):
    global is_playing
    is_playing = True
    play_pause_btn.configure(text="⏸ PAUSE", fg_color=current_theme["primary"])
    status_label.configure(text=f"▶ Playing: {song['title']}")
    _update_playlist_highlights()
    start_disk_rotation()
    load_album_art(song.get("image_url"))


def toggle_play_pause():
    global is_playing
    if not current_playlist: return
    if not audio_player.is_loaded():
        _load_and_play()
        return
    if is_playing:
        audio_player.pause()
        is_playing = False
        play_pause_btn.configure(text="▶ PLAY", fg_color=current_theme["primary"])
        status_label.configure(text="⏸ Playback Paused")
        stop_disk_rotation()
    else:
        audio_player.resume()
        is_playing = True
        play_pause_btn.configure(text="⏸ PAUSE", fg_color=current_theme["primary"])
        status_label.configure(text="▶ Playing")
        start_disk_rotation()
    _update_playlist_highlights()


def stop():
    global is_playing
    audio_player.stop()
    is_playing = False
    play_pause_btn.configure(text="▶ PLAY", fg_color=current_theme["primary"])
    status_label.configure(text="⏹ Playback Stopped")
    time_current_label.configure(text="00:00")
    seek_slider.set(0)
    stop_disk_rotation()
    _update_playlist_highlights()


def next_song():
    global current_index
    if not current_playlist: return
    if repeat_mode == "one":
        _load_and_play()
        return
    if is_shuffle and len(current_playlist) > 1:
        next_idx = current_index
        while next_idx == current_index: next_idx = random.randint(0, len(current_playlist) - 1)
        current_index = next_idx
        _load_and_play()
        return
    if current_index < len(current_playlist) - 1:
        current_index += 1
        _load_and_play()
    elif repeat_mode == "all":
        current_index = 0
        _load_and_play()
    else:
        stop()
        status_label.configure(text="🏁 Playlist Finished")


def previous_song():
    global current_index
    if not current_playlist: return
    if audio_player.get_time() > 3000:
        audio_player.set_position(0.0)
        return
    if current_index > 0:
        current_index -= 1
        _load_and_play()
    elif repeat_mode == "all":
        current_index = len(current_playlist) - 1
        _load_and_play()


audio_player.set_on_end_callback(lambda: app.after(0, next_song))


# Album Art & Vinyl Disc
def load_album_art(url):
    if not url: return
    if url in album_art_cache:
        _apply_album_art_to_disc(album_art_cache[url])
        return
    threading.Thread(target=lambda: _art_worker(url), daemon=True).start()


def _art_worker(url: str):
    try:
        resp = requests.get(url, timeout=8)
        resp.raise_for_status()
        img = Image.open(io.BytesIO(resp.content))
    except Exception: return
    album_art_cache[url] = img
    app.after(0, lambda: _apply_album_art_to_disc(img))


def _apply_album_art_to_disc(img: Image.Image):
    global current_disc_pil, cached_art_img
    cached_art_img = img
    current_disc_pil = build_composite_disc(img)
    if not is_playing: _update_disc_label(current_disc_pil)


def _update_disc_label(pil_img: Image.Image):
    ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(DISC_SIZE, DISC_SIZE))
    disk_label.configure(image=ctk_img)
    disk_label.image = ctk_img


# Rotation & Visualizer
def start_disk_rotation():
    stop_disk_rotation()
    _rotate_step()


def stop_disk_rotation():
    global rotate_timer
    if rotate_timer is not None:
        app.after_cancel(rotate_timer)
        rotate_timer = None
    eq_visualizer_label.configure(text=" ▂▃▅▇ ")


def _rotate_step():
    global rotation_angle, rotate_timer, eq_frame_idx
    if not is_playing:
        rotate_timer = None
        eq_visualizer_label.configure(text=" ▂▃▅▇ ")
        return
    rotation_angle = (rotation_angle + 3) % 360
    rotated = current_disc_pil.rotate(rotation_angle, resample=Image.Resampling.BICUBIC)
    _update_disc_label(rotated)
    eq_frame_idx = (eq_frame_idx + 1) % len(EQ_FRAMES)
    eq_visualizer_label.configure(text=EQ_FRAMES[eq_frame_idx])
    rotate_timer = app.after(33, _rotate_step)


# Progress Timer Loop
def update_ui_loop():
    if is_playing and audio_player.is_loaded() and not is_seeking:
        seek_slider.set(audio_player.get_position() * 1000.0)
        time_current_label.configure(text=format_time(audio_player.get_time()))
        dur = audio_player.get_duration()
        if dur > 0: time_total_label.configure(text=format_time(dur))
    app.after(250, update_ui_loop)


update_ui_loop()
app.mainloop()