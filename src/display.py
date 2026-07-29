import M5 # type: ignore


_display: M5.Display = M5.Display

_default_clear_color: int = 0x000000

_canvas: object | None = None
_target: object = _display

WIDTH: int = _display.width()
HEIGHT: int = _display.height()


def initialize_canvas(w: int = WIDTH, h: int = HEIGHT) -> None:
    global _canvas, _target
    _canvas = _display.newCanvas(w, h)


def use_canvas() -> None:
    global _target, _canvas
    if _canvas is None:
        initialize_canvas()
    _target = _canvas


def use_display() -> None:
    global _target
    _target = _display


def flush_canvas(x: int = 0, y: int = 0) -> None:
    _canvas.push(x, y)


def clear_canvas(color: int = -1):
    if _canvas is not None:
        color_: int = _default_clear_color if color == -1 else color
        _canvas.fillScreen(color_)


def set_brightness(level: int): # 0 - 255 range
    _display.setBrightness(level)


def get_brightness() -> int: # 0 - 255 range
    return _display.getBrightness()


def fill_screen(color: int = 0x000000):
    _target.fillScreen(color)


def clear_screen():
    _target.fillScreen(_default_clear_color)


def set_clear_color(color: int):
    global _default_clear_color
    _default_clear_color = color


def text(text: str, x: int = 0, y: int = 0, size: float = 2.0, color: int = 0xFFFFFF, background_color: int = -1):
    _target.setTextSize(size)
    _target.setTextColor(color, background_color)
    if background_color != -1:
        _target.setTextColor(color, background_color)
    else:
        _target.setTextColor(color)
    _target.drawString(text, x, y)


def draw_pixel(x: int, y: int, color: int = 0xFFFFFF):
    _target.drawPixel(x, y, color)


def draw_line(x_from: int, y_from: int, x_to: int, y_to: int, color: int = 0xFFFFFF):
    _target.drawLine(x_from, y_from, x_to, y_to, color)


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
