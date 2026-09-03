import display
import localtime
from config import (
    SERVICE__AUTO_BRIGHTNESS_DAY_BRIGHTNESS,
    SERVICE__AUTO_BRIGHTNESS_NIGHT_BRIGHTNESS,
    SERVICE__AUTO_BRIGHTNESS_DAY_START_HOUR,
    SERVICE__AUTO_BRIGHTNESS_NIGHT_START_HOUR,
)


def initialize():
    pass


def deinitialize():
    pass


def update():
    if not localtime.hour_changed():
        return

    current_hour: int = localtime.hour()

    if current_hour == SERVICE__AUTO_BRIGHTNESS_DAY_START_HOUR:
        clamped_brightness: int = max(10, min(255, SERVICE__AUTO_BRIGHTNESS_DAY_BRIGHTNESS))
        display.set_brightness(clamped_brightness)
    elif current_hour == SERVICE__AUTO_BRIGHTNESS_NIGHT_START_HOUR:
        clamped_brightness: int = max(10, min(255, SERVICE__AUTO_BRIGHTNESS_NIGHT_BRIGHTNESS))
        display.set_brightness(clamped_brightness)
