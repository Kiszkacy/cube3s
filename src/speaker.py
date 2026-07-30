import M5 # type: ignore
# IMPORTANT: only speaker or mic can be enabled at a time, because they share the same bus, there are no safety checks in either module

DEFAULT_VOLUME: int = 64 # 0 - 255
DEFAULT_SAMPLE_RATE: int = 16000 # hz
BEEP_TONE: int = 1000 # hz ~100 - 10000
BEEP_TONE_HIGH: int = 1400 # hz, second note of the double beep
BEEP_DURATION: int = 80 # ms


_speaker = M5.Speaker


def enable(volume: int = DEFAULT_VOLUME):
    if not _speaker.isRunning():
        _speaker.begin()
    _speaker.setVolume(volume)
    print("[SPEAKER] enabled.")


def disable():
    _speaker.end()
    print("[SPEAKER] disabled.")


def is_enabled() -> bool:
    return _speaker.isRunning()


def set_volume(volume: int): # 0 - 255
    _speaker.setVolume(volume)


def get_volume() -> int: # 0 - 255
    return _speaker.getVolume()


# TODO: what does channel do exactly ?
def tone(frequency: int, duration_ms: int, volume: int = -1, channel: int = 0, stop_current_sound: bool = True): # frequency ~100 - 10000 hz
    if volume != -1:
        clamped_volume: int = max(0, min(255, volume))
        _speaker.setVolume(clamped_volume)
    _speaker.tone(frequency, duration_ms, channel, stop_current_sound)


def stop():
    _speaker.stop()


def play_raw(buffer, sample_rate: int = DEFAULT_SAMPLE_RATE, stereo: bool = False) -> bool: # should be able to play mic.record() output directly
    return _speaker.playRaw(buffer, sample_rate, stereo)


def is_playing() -> bool:
    return _speaker.isPlaying()


def beep(volume: int = -1):
    tone(BEEP_TONE, BEEP_DURATION, volume)


def double_beep(volume: int = -1):
    tone(BEEP_TONE, BEEP_DURATION, volume, stop_current_sound=True)
    tone(BEEP_TONE_HIGH, BEEP_DURATION, stop_current_sound=False) # queue second beep
