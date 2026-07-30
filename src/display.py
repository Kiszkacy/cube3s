import M5 # type: ignore
import image


_display: M5.Display = M5.Display

_default_clear_color: int = 0x000000

_canvas: object | None = None
_target: object = _display

WIDTH: int = _display.width()
HEIGHT: int = _display.height()

FONTS = getattr(_display, "FONTS", None)
FONT_NAMES: tuple = tuple(
    sorted(name for name in dir(FONTS) if not name.startswith("_"))
) if FONTS is not None else ()

DEFAULT_TEXT_SIZE: float = 2.0
DEFAULT_TEXT_COLOR: int = 0xFFFFFF
DEFAULT_TEXT_BACKGROUND_COLOR: int = -1 # -1 => should mean transparent background
DEFAULT_TEXT_ANCHOR: str = "top-left"

_active_font_name: str | None = None # None => currently uses default font
_text_size: float = DEFAULT_TEXT_SIZE
_text_color: int = DEFAULT_TEXT_COLOR
_text_background_color: int = DEFAULT_TEXT_BACKGROUND_COLOR
_text_anchor: str = DEFAULT_TEXT_ANCHOR

VERTICAL_ANCHORS: tuple = ("top", "middle", "bottom")
HORIZONTAL_ANCHORS: tuple = ("left", "center", "right")


def initialize_canvas(width: int = WIDTH, height: int = HEIGHT):
    global _canvas
    _canvas = _display.newCanvas(width, height, 16, True)


def use_canvas():
    global _target, _canvas
    if _canvas is None:
        initialize_canvas()
    _target = _canvas


def use_display():
    global _target
    _target = _display


def flush_canvas(x: int = 0, y: int = 0):
    _canvas.push(x, y)


def clear_canvas(color: int = -1):
    if _canvas is not None:
        color_: int = _default_clear_color if color == -1 else color
        _canvas.fillScreen(color_)


def set_brightness(level: int): # 0 - 255
    _display.setBrightness(level)


def get_brightness() -> int: # 0 - 255
    return _display.getBrightness()


def fill_screen(color: int = 0x000000):
    _target.fillScreen(color)


def clear_screen():
    _target.fillScreen(_default_clear_color)


def set_clear_color(color: int):
    global _default_clear_color
    _default_clear_color = color


def get_current_font_name() -> str:
    return _active_font_name if _active_font_name is not None else "default"


def _apply_font_by_name(name: str) -> bool:
    font: object = getattr(FONTS, name, None) if FONTS is not None else None
    if font is not None:
        _target.setFont(font)
        return True
    return False


def set_font(name: str) -> bool: # returns True if the font was successfully set, False if the font name is invalid
    global _active_font_name
    if _apply_font_by_name(name):
        _active_font_name = name
        return True
    return False


def reset_font():
    global _active_font_name
    _active_font_name = None
    _target.unloadFont() # should restore default font


def set_text_size(size: float):
    global _text_size
    _text_size = size


def set_text_color(color: int, background_color: int = -1):
    global _text_color, _text_background_color
    _text_color = color
    _text_background_color = background_color


def set_text_anchor(anchor: str):
    global _text_anchor
    _text_anchor = anchor


def set_text_style(size: float | None = None, color: int | None = None, background_color: int | None = None, anchor: str | None = None, font_name: str | None = None):
    global _text_size, _text_color, _text_background_color, _text_anchor
    if size is not None:
        _text_size = size
    if color is not None:
        _text_color = color
    if background_color is not None:
        _text_background_color = background_color
    if anchor is not None:
        _text_anchor = anchor
    if font_name is not None:
        set_font(font_name)


def reset_text_style() -> None:
    global _text_size, _text_color, _text_background_color, _text_anchor
    _text_size = DEFAULT_TEXT_SIZE
    _text_color = DEFAULT_TEXT_COLOR
    _text_background_color = DEFAULT_TEXT_BACKGROUND_COLOR
    _text_anchor = DEFAULT_TEXT_ANCHOR
    reset_font()


# TODO: quite unoptimized, add a separate simple text drawing functions
def draw_text(text: str, x: int = 0, y: int = 0, size: float | None = None, color: int | None = None, background_color: int | None = None, anchor: str | None = None, font_name: str | None = None):
    size = _text_size if size is None else size
    color = _text_color if color is None else color
    background_color = _text_background_color if background_color is None else background_color
    anchor = _text_anchor if anchor is None else anchor

    if font_name is not None:
        _apply_font_by_name(font_name)

    _target.setTextSize(size)

    if background_color != -1:
        _target.setTextColor(color, background_color)
    else:
        _target.setTextColor(color, color) # passing same color for both text and background results in transparent background

    font_height: int = _target.fontHeight()
    vertical: str = "middle"
    horizontal: str = "center"
    for part in anchor.split("-"):
        if part in VERTICAL_ANCHORS:
            vertical = part
        elif part in HORIZONTAL_ANCHORS:
            horizontal = part

    if vertical == "middle":
        y -= font_height // 2
    elif vertical == "bottom":
        y -= font_height

    if horizontal == "center":
        _target.drawCenterString(text, x, y)
    elif horizontal == "right":
        _target.drawRightString(text, x, y)
    else:
        _target.drawString(text, x, y)

    if font_name is not None:
        if _active_font_name is not None:
            _apply_font_by_name(_active_font_name)
        else:
            _target.unloadFont()


def draw_pixel(x: int, y: int, color: int = 0xFFFFFF):
    _target.drawPixel(x, y, color)


def draw_line(x_from: int, y_from: int, x_to: int, y_to: int, color: int = 0xFFFFFF):
    _target.drawLine(x_from, y_from, x_to, y_to, color)


# TODO: add helper anchor points args for shapes ?
def draw_rect(x: int, y: int, width: int, height: int, color: int = 0xFFFFFF, fill: bool = False):
    if fill:
        _target.fillRect(x, y, width, height, color)
    else:
        _target.drawRect(x, y, width, height, color)


def draw_round_rect(x: int, y: int, width: int, height: int, radius: int, color: int = 0xFFFFFF, fill: bool = False):
    if fill:
        _target.fillRoundRect(x, y, width, height, radius, color)
    else:
        _target.drawRoundRect(x, y, width, height, radius, color)


def draw_circle(x: int, y: int, radius: int, color: int = 0xFFFFFF, fill: bool = False):
    if fill:
        _target.fillCircle(x, y, radius, color)
    else:
        _target.drawCircle(x, y, radius, color)


def draw_triangle(x0: int, y0: int, x1: int, y1: int, x2: int, y2: int, color: int = 0xFFFFFF, fill: bool = False):
    if fill:
        _target.fillTriangle(x0, y0, x1, y1, x2, y2, color)
    else:
        _target.drawTriangle(x0, y0, x1, y1, x2, y2, color)


def draw_image(image_: image.Image, width: int, height: int, x: int = 0, y: int = 0):
    _target.show(image_, x, y, width, height)
