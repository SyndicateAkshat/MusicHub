import html
import os
import threading
import requests

from kivy.app import App
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.graphics import Color, Rectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.slider import Slider
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput

# Theme Color Presets
THEMES = {
    "🌸 Soft Coral Peach": {
        "bg": (0.07, 0.09, 0.13, 1),
        "panel": (0.10, 0.13, 0.18, 1),
        "primary": (1.0, 0.46, 0.46, 1),
        "secondary": (1.0, 0.42, 0.42, 1),
        "text": (0.90, 0.93, 0.95, 1),
    },
    "💚 Emerald Green": {
        "bg": (0.07, 0.09, 0.13, 1),
        "panel": (0.10, 0.13, 0.18, 1),
        "primary": (0.18, 0.80, 0.44, 1),
        "secondary": (0.06, 0.72, 0.50, 1),
        "text": (0.90, 0.93, 0.95, 1),
    },
    "💜 Cyberpunk Neon": {
        "bg": (0.04, 0.05, 0.06, 1),
        "panel": (0.08, 0.09, 0.13, 1),
        "primary": (0.42, 0.36, 0.90, 1),
        "secondary": (0.0, 0.81, 0.79, 1),
        "text": (1.0, 1.0, 1.0, 1),
    },
    "💙 Electric Cyan": {
        "bg": (0.06, 0.09, 0.16, 1),
        "panel": (0.12, 0.16, 0.23, 1),
        "primary": (0.0, 0.81, 0.79, 1),
        "secondary": (0.22, 0.74, 0.97, 1),
        "text": (0.97, 0.98, 0.99, 1),
    },
}


class MusicHubKivyApp(App):
    def build(self):
        self.title = "MusicHub Mobile"
        self.current_theme = THEMES["🌸 Soft Coral Peach"]
        self.playlist = []
        self.current_index = 0
        self.sound = None
        self.is_playing = False

        # Main Layout Root
        self.root_layout = BoxLayout(orientation="vertical", padding=15, spacing=10)
        with self.root_layout.canvas.before:
            Color(*self.current_theme["bg"])
            self.bg_rect = Rectangle(size=self.root_layout.size, pos=self.root_layout.pos)
        self.root_layout.bind(size=self._update_rect, pos=self._update_rect)

        # Header Bar
        header = BoxLayout(orientation="horizontal", size_hint_y=None, height=45, spacing=10)
        self.brand_title = Label(
            text="🎵 MusicHub Mobile",
            font_size=20,
            bold=True,
            color=self.current_theme["secondary"],
            halign="left",
            size_hint_x=0.6,
        )
        self.theme_spinner = Spinner(
            text="🌸 Soft Coral Peach",
            values=list(THEMES.keys()),
            size_hint_x=0.4,
            background_color=self.current_theme["primary"],
        )
        self.theme_spinner.bind(text=self.on_theme_change)

        header.add_widget(self.brand_title)
        header.add_widget(self.theme_spinner)
        self.root_layout.add_widget(header)

        # Search Bar
        search_box = BoxLayout(orientation="horizontal", size_hint_y=None, height=45, spacing=8)
        self.search_input = TextInput(
            hint_text="🔍 Search songs, artists…",
            multiline=False,
            size_hint_x=0.75,
            background_color=(0.15, 0.18, 0.24, 1),
            foreground_color=(1, 1, 1, 1),
        )
        self.search_input.bind(on_text_validate=self.on_search)

        search_btn = Button(
            text="Search",
            size_hint_x=0.25,
            background_color=self.current_theme["primary"],
            bold=True,
        )
        search_btn.bind(on_press=self.on_search)

        search_box.add_widget(self.search_input)
        search_box.add_widget(search_btn)
        self.root_layout.add_widget(search_box)

        # Status Label
        self.status_label = Label(
            text="✨ Ready to play audio",
            font_size=14,
            color=(0.6, 0.65, 0.7, 1),
            size_hint_y=None,
            height=30,
        )
        self.root_layout.add_widget(self.status_label)

        # Results Scroll Area
        self.scroll_view = ScrollView(size_hint=(1, 1))
        self.results_layout = BoxLayout(orientation="vertical", size_hint_y=None, spacing=5)
        self.results_layout.bind(minimum_height=self.results_layout.setter("height"))
        self.scroll_view.add_widget(self.results_layout)
        self.root_layout.add_widget(self.scroll_view)

        # Now Playing Header
        self.now_playing_title = Label(
            text="No Song Selected",
            font_size=16,
            bold=True,
            color=self.current_theme["text"],
            size_hint_y=None,
            height=30,
        )
        self.root_layout.add_widget(self.now_playing_title)

        # Playback Controls Bar
        controls = BoxLayout(orientation="horizontal", size_hint_y=None, height=50, spacing=10)
        self.prev_btn = Button(text="⏮", background_color=self.current_theme["primary"])
        self.prev_btn.bind(on_press=self.prev_song)

        self.play_btn = Button(text="▶ PLAY", background_color=self.current_theme["primary"], bold=True)
        self.play_btn.bind(on_press=self.toggle_play)

        self.next_btn = Button(text="⏭", background_color=self.current_theme["primary"])
        self.next_btn.bind(on_press=self.next_song)

        controls.add_widget(self.prev_btn)
        controls.add_widget(self.play_btn)
        controls.add_widget(self.next_btn)
        self.root_layout.add_widget(controls)

        # Progress Slider
        self.seek_slider = Slider(min=0, max=100, value=0, size_hint_y=None, height=35)
        self.root_layout.add_widget(self.seek_slider)

        Clock.schedule_interval(self.update_progress, 0.5)
        return self.root_layout

    def _update_rect(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size

    def on_theme_change(self, spinner, text):
        if text in THEMES:
            self.current_theme = THEMES[text]
            self.brand_title.color = self.current_theme["secondary"]
            self.theme_spinner.background_color = self.current_theme["primary"]
            self.play_btn.background_color = self.current_theme["primary"]
            self.prev_btn.background_color = self.current_theme["primary"]
            self.next_btn.background_color = self.current_theme["primary"]

    def on_search(self, *args):
        query = self.search_input.text.strip()
        if not query:
            return
        self.status_label.text = "🔍 Searching music online…"
        threading.Thread(target=self._search_worker, args=(query,), daemon=True).start()

    def _search_worker(self, query):
        try:
            resp = requests.get(
                "https://itunes.apple.com/search",
                params={"term": query, "media": "music", "entity": "song", "limit": 20},
                timeout=6,
            )
            if resp.status_code == 200:
                results = resp.json().get("results", [])
                songs = []
                for item in results:
                    url = item.get("previewUrl")
                    if url:
                        songs.append({
                            "title": html.unescape(item.get("trackName") or "Unknown"),
                            "artist": html.unescape(item.get("artistName") or "Unknown"),
                            "url": url,
                        })
                Clock.schedule_once(lambda dt: self._populate_results(songs))
        except Exception as e:
            Clock.schedule_once(lambda dt: self.set_status(f"❌ Error: {e}"))

    def set_status(self, text):
        self.status_label.text = text

    def _populate_results(self, songs):
        self.playlist = songs
        self.results_layout.clear_widgets()
        if not songs:
            self.status_label.text = "⚠️ No songs found"
            return

        self.status_label.text = f"✨ Found {len(songs)} tracks"
        for i, song in enumerate(songs):
            btn = Button(
                text=f"{i+1}. {song['title']} - {song['artist']}",
                size_hint_y=None,
                height=45,
                halign="left",
                valign="center",
                background_color=(0.15, 0.19, 0.26, 1),
            )
            btn.bind(on_press=lambda b, idx=i: self.play_song_at(idx))
            self.results_layout.add_widget(btn)

    def play_song_at(self, idx):
        if not self.playlist or idx < 0 or idx >= len(self.playlist):
            return
        self.current_index = idx
        song = self.playlist[idx]
        self.now_playing_title.text = f"▶ {song['title']} ({song['artist']})"

        if self.sound:
            self.sound.stop()
            self.sound.unload()

        self.sound = SoundLoader.load(song["url"])
        if self.sound:
            self.sound.play()
            self.is_playing = True
            self.play_btn.text = "⏸ PAUSE"

    def toggle_play(self, *args):
        if not self.sound and self.playlist:
            self.play_song_at(0)
            return

        if self.sound:
            if self.is_playing:
                self.sound.stop()
                self.is_playing = False
                self.play_btn.text = "▶ PLAY"
            else:
                self.sound.play()
                self.is_playing = True
                self.play_btn.text = "⏸ PAUSE"

    def next_song(self, *args):
        if self.playlist and self.current_index < len(self.playlist) - 1:
            self.play_song_at(self.current_index + 1)

    def prev_song(self, *args):
        if self.playlist and self.current_index > 0:
            self.play_song_at(self.current_index - 1)

    def update_progress(self, dt):
        if self.sound and self.is_playing and self.sound.length > 0:
            pos = self.sound.get_pos()
            self.seek_slider.value = (pos / self.sound.length) * 100


if __name__ == "__main__":
    MusicHubKivyApp().run()
