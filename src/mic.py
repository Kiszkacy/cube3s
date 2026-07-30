import array
import time
import M5 # type: ignore
# IMPORTANT: only speaker or mic can be enabled at a time, because they share the same bus, there are no safety checks in either module

DEFAULT_SAMPLE_RATE: int = 16000 # hz


_mic = M5.Mic


def enable():
    if _mic.isEnabled():
        return
    _mic.begin()
    print("[MIC] enabled.")


def disable():
    _mic.end()
    print("[MIC] disabled.")


def is_enabled() -> bool:
    return _mic.isEnabled()


def is_recording() -> bool:
    return _mic.isRecording()


def create_buffer(seconds: float, stereo: bool = False, sample_rate: int = DEFAULT_SAMPLE_RATE) -> array.array:
    channels: int = 2 if stereo else 1 # stereo interleaves two samples per frame (L, R), so it needs twice the space
    sample_count: int = int(seconds * sample_rate) * channels
    return array.array("h", [0] * sample_count) # "h" here means => use signed 16-bit integers


def record(buffer: array.array, stereo: bool = False, sample_rate: int = DEFAULT_SAMPLE_RATE) -> bool:
    return _mic.record(buffer, sample_rate, stereo)


def record__B(seconds: float, poll_interval_ms: int = 10, stereo: bool = False, sample_rate: int = DEFAULT_SAMPLE_RATE) -> array.array | None:
    buffer: array.array = create_buffer(seconds, stereo, sample_rate)
    if not record(buffer, stereo, sample_rate):
        return None
    while _mic.isRecording():
        time.sleep_ms(poll_interval_ms)
    return buffer

