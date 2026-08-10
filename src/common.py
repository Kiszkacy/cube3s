from display import HEIGHT, set_brightness


def set_brightness_from_vertical_position(y: int) -> int:
    brightness: int = int(255 * (1.0 - (y / HEIGHT)))
    clamped_brightness: int = max(10, min(255, brightness))
    set_brightness(clamped_brightness)
    return clamped_brightness
