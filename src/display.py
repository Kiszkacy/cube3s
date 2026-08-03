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

# XXYY bits, XX = vertical, YY = horizontal
TOP_LEFT: int = 0b0000
TOP_CENTER: int = 0b0001
TOP_RIGHT: int = 0b0010
MIDDLE_LEFT: int = 0b0100
MIDDLE_CENTER: int = 0b0101
MIDDLE_RIGHT: int = 0b0110
BOTTOM_LEFT: int = 0b1000
BOTTOM_CENTER: int = 0b1001
BOTTOM_RIGHT: int = 0b1010

_VERTICAL_TOP: int = 0
_VERTICAL_MIDDLE: int = 1
_HORIZONTAL_MASK: int = 0b11
_HORIZONTAL_CENTER: int = 1
_HORIZONTAL_RIGHT: int = 2

DEFAULT_TEXT_SIZE: float = 2.0
DEFAULT_TEXT_COLOR: int = 0xFFFFFF
DEFAULT_TEXT_BACKGROUND_COLOR: int = -1 # -1 => means transparent background
DEFAULT_TEXT_ANCHOR: int = TOP_LEFT

_active_font_name: str | None = None # None => currently uses default font
_text_size: float = DEFAULT_TEXT_SIZE
_text_color: int = DEFAULT_TEXT_COLOR
_text_background_color: int = DEFAULT_TEXT_BACKGROUND_COLOR
_text_anchor: int = DEFAULT_TEXT_ANCHOR

_brightness: int = _display.getBrightness() # mirrors the panel, so a repeated set_brightness() costs nothing


def _initialize_canvas(width: int = WIDTH, height: int = HEIGHT, psram: bool = True):
    global _canvas, _target
    was_active: bool = _target is _canvas
    if _canvas is not None:
        _canvas.delete() # remove old canvas to avoid memory leak
    _canvas = _display.newCanvas(width, height, 16, psram)
    if was_active:
        _target = _canvas


def use_canvas():
    global _target, _canvas
    if _canvas is None:
        _initialize_canvas()
    _target = _canvas


def use_display():
    global _target
    _target = _display


def flush_canvas(x: int = 0, y: int = 0):
    if _canvas is not None:
        _canvas.push(x, y)


def clear_canvas(color: int = -1):
    if _canvas is not None:
        color_: int = _default_clear_color if color == -1 else color
        _canvas.fillScreen(color_)


def create_canvas(width: int, height: int, psram: bool = False) -> object: # psram=False => small canvases are faster in internal ram
    return _display.newCanvas(width, height, 16, psram)


def delete_canvas(canvas: object): # must be manually called to avoid memory leak
    canvas.delete()


def push_canvas(canvas: object, x: int = 0, y: int = 0):
    canvas.push(x, y)


def set_target(target: object):
    global _target
    _target = target


def fill_target(target: object, color: int = 0x000000):
    target.fillScreen(color)


def clear_target(target: object):
    target.fillScreen(_default_clear_color)


def target() -> object:
    return _target


def display_target() -> object:
    return _display


def start_write(): # batches direct-to-display drawing into a single spi transaction
    _display.startWrite()


def end_write():
    _display.endWrite()


def set_brightness(level: int): # 0 - 255
    global _brightness
    if level == _brightness:
        return
    _brightness = level
    _display.setBrightness(level)


def get_brightness() -> int: # 0 - 255
    return _brightness


def get_brightness__RS() -> int: # 0 - 255, asks the panel directly instead of relying on the cached value
    global _brightness
    _brightness = _display.getBrightness()
    return _brightness


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


def text_width(text: str, size: float | None = None) -> int: # width the text would take at size, or at the default text size
    _target.setTextSize(_text_size if size is None else size)
    return _target.textWidth(text)


def font_height(size: float | None = None) -> int: # line height of the current font at size, or at the default text size
    _target.setTextSize(_text_size if size is None else size)
    return _target.fontHeight()


def set_text_size(size: float):
    global _text_size
    _text_size = size


def set_text_color(color: int, background_color: int = -1):
    global _text_color, _text_background_color
    _text_color = color
    _text_background_color = background_color


def set_text_anchor(anchor: int):
    global _text_anchor
    _text_anchor = anchor


def set_text_style(size: float | None = None, color: int | None = None, background_color: int | None = None, anchor: int | None = None, font_name: str | None = None):
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


# TODO: each call to draw_text() sets the text size and color, which is inefficient when drawing many texts with the same style
# TODO: issue comes with the ability to change current target, so even tracking the styling is not a good solution
# TODO: for now I think this is acceptable
def draw_text(text: str, x: int = 0, y: int = 0, size: float | None = None, color: int | None = None, background_color: int | None = None, anchor: int | None = None, font_name: str | None = None):
    size = _text_size if size is None else size
    color = _text_color if color is None else color
    background_color = _text_background_color if background_color is None else background_color
    anchor = _text_anchor if anchor is None else anchor

    overrides_font: bool = font_name is not None and font_name != _active_font_name
    if overrides_font:
        _apply_font_by_name(font_name)

    _target.setTextSize(size)

    if background_color != -1:
        _target.setTextColor(color, background_color)
    else:
        _target.setTextColor(color, color) # passing same color for both text and background results in transparent background

    vertical: int = anchor >> 2
    if vertical != _VERTICAL_TOP:
        height: int = _target.fontHeight()
        y -= height // 2 if vertical == _VERTICAL_MIDDLE else height

    horizontal: int = anchor & _HORIZONTAL_MASK
    if horizontal == _HORIZONTAL_CENTER:
        _target.drawCenterString(text, x, y)
    elif horizontal == _HORIZONTAL_RIGHT:
        _target.drawRightString(text, x, y)
    else:
        _target.drawString(text, x, y)

    if overrides_font:
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


# TODO: rename radius to border_radius/corner_radius ?
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


def draw_jpg_bytes(jpg_bytes: bytes, x: int = 0, y: int = 0):
    _target.drawJpg(jpg_bytes, x, y)
