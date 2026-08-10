import display
import touch


# TODO: add more colors
COLOR_BLACK: int = 0x000000
COLOR_DARK_GRAY: int = 0x444444
COLOR_WHITE: int = 0xFFFFFF

SCREEN_PADDING: int = 0
SEPARATOR_COLOR: int = COLOR_DARK_GRAY # dark gray

DEFAULT_TEXT_SIZE: float = 2.0
DEFAULT_TEXT_COLOR: int = COLOR_WHITE

BUTTON_FILL_COLOR: int = 0x004040 # dark cyan
BUTTON_BORDER_COLOR: int = COLOR_WHITE
BUTTON_TEXT_COLOR: int = COLOR_WHITE
BUTTON_TEXT_SIZE: float = 2.0
BUTTON_CORNER_RADIUS: int = 4

BAR_BACKGROUND_COLOR: int = 0x333333 # very dark gray


def rect(x: int, y: int, width: int, height: int) -> tuple:
    return x, y, width, height


def rect_around(center_x_: int, center_y_: int, width: int, height: int) -> tuple:
    return center_x_ - width//2, center_y_ - height//2, width, height


def center_x(rect_: tuple) -> int:
    return rect_[0] + rect_[2]//2


def center_y(rect_: tuple) -> int:
    return rect_[1] + rect_[3]//2


def is_inside(x: int, y: int, rect_: tuple) -> bool:
    return (rect_[0] <= x <= rect_[0] + rect_[2]) and (rect_[1] <= y <= rect_[1] + rect_[3])


def is_inside_which(x: int, y: int, rects: list[tuple]) -> int:
    for index, rect_ in enumerate(rects):
        if is_inside(x, y, rect_):
            return index
    return -1


def draw_button(
    rect_: tuple, label: str | None = None, fill_color: int = BUTTON_FILL_COLOR, border_color: int = BUTTON_BORDER_COLOR, text_color: int = BUTTON_TEXT_COLOR, text_size: float = BUTTON_TEXT_SIZE, radius: int = BUTTON_CORNER_RADIUS
):
    if fill_color != -1:
        display.draw_round_rect(rect_[0], rect_[1], rect_[2], rect_[3], radius=radius, color=fill_color, fill=True)
    if border_color != -1:
        display.draw_round_rect(rect_[0], rect_[1], rect_[2], rect_[3], radius=radius, color=border_color)

    if label is not None:
        display.draw_text(label, x=rect_[0] + rect_[2]//2, y=rect_[1] + rect_[3]//2, size=text_size, anchor=display.MIDDLE_CENTER, color=text_color, background_color=fill_color)


def draw_separator(x: int, y_top: int, height: int = 16, color: int = SEPARATOR_COLOR):
    display.draw_line(x, y_top, x, y_top+height, color=color)


def draw_bar(rect_: tuple, progress: float, color: int, background_color: int = BAR_BACKGROUND_COLOR):
    radius: int = rect_[3]//2
    if background_color != -1:
        display.draw_round_rect(rect_[0], rect_[1], rect_[2], rect_[3], radius=radius, color=background_color, fill=True)
    if progress <= 0.0:
        return
    filled_width: int = rect_[3] if progress >= 1.0 else max(rect_[3], int(rect_[2]*progress))
    display.draw_round_rect(rect_[0], rect_[1], min(rect_[2], filled_width), rect_[3], radius=radius, color=color, fill=True)
