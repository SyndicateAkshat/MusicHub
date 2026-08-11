import vlc


class AudioPlayer:
    def __init__(self):
        self._instance = vlc.Instance("--quiet")
        self._player = self._instance.media_player_new()
        self._loaded_url = None
        self._on_end_cb = None
        self._on_error_cb = None

        em = self._player.event_manager()
        em.event_attach(vlc.EventType.MediaPlayerEndReached, self._evt_cb(lambda: self._on_end_cb))
        em.event_attach(vlc.EventType.MediaPlayerEncounteredError, self._evt_cb(lambda: self._on_error_cb))

    def _evt_cb(self, get_fn):
        def handler(evt):
            fn = get_fn()
            if fn:
                try:
                    fn()
                except Exception:
                    pass
        return handler

    def set_on_end_callback(self, cb): self._on_end_cb = cb
    def set_on_error_callback(self, cb): self._on_error_cb = cb

    def load(self, url: str) -> None:
        self.stop()
        self._player.set_media(self._instance.media_new(url))
        self._loaded_url = url

    def is_loaded(self) -> bool: return self._loaded_url is not None
    def play(self) -> None: self._player.play()
    def pause(self) -> None: self._player.set_pause(1)
    def resume(self) -> None: self._player.set_pause(0)
    def stop(self) -> None:
        self._player.stop()
        self._loaded_url = None

    def is_playing(self) -> bool: return self._player.is_playing() == 1
    def is_paused(self) -> bool: return self._player.get_state() == vlc.State.Paused
    def get_position(self) -> float: return max(self._player.get_position(), 0.0)
    def set_position(self, pos: float) -> None: self._player.set_position(max(0.0, min(1.0, float(pos))))
    def get_time(self) -> int: return max(self._player.get_time(), 0)
    def get_duration(self) -> int: return max(self._player.get_length(), 0)
    def get_volume(self) -> int: return max(self._player.audio_get_volume(), 0)
    def set_volume(self, volume: int) -> None: self._player.audio_set_volume(max(0, min(100, int(volume))))