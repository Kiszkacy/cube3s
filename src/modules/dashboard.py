import display
import localtime
import mqtt
import router
import touch
import ui
from config import DASHBOARD__MQTT_INPUT_TOPIC
from ui import COLOR_WHITE


SERVICES: tuple[str, ...] = ("auto_brightness",)


DASHBOARD_PADDING: int = 8

BOTTOM_PANEL_COLS: int = 5
BOTTOM_PANEL_ROWS: int = 2
BOTTOM_PANEL_GAP: int = 4
BOTTOM_PANEL_HEIGHT: int = 80
BOTTOM_PANEL_Y: int = display.HEIGHT - BOTTOM_PANEL_HEIGHT
BOTTOM_PANEL_INNER_WIDTH: int = display.WIDTH - 2*DASHBOARD_PADDING - (BOTTOM_PANEL_COLS-1)*BOTTOM_PANEL_GAP
BOTTOM_PANEL_INNER_HEIGHT: int = BOTTOM_PANEL_HEIGHT - 2*DASHBOARD_PADDING - (BOTTOM_PANEL_ROWS-1)*BOTTOM_PANEL_GAP
BOTTOM_PANEL_CELL_WIDTH: int = BOTTOM_PANEL_INNER_WIDTH // BOTTOM_PANEL_COLS
BOTTOM_PANEL_CELL_HEIGHT: int = BOTTOM_PANEL_INNER_HEIGHT // BOTTOM_PANEL_ROWS


def bottom_panel_cell(col: int, row: int) -> tuple:
    return ui.rect(
        DASHBOARD_PADDING + col*(BOTTOM_PANEL_CELL_WIDTH + BOTTOM_PANEL_GAP),
        BOTTOM_PANEL_Y + DASHBOARD_PADDING + row*(BOTTOM_PANEL_CELL_HEIGHT + BOTTOM_PANEL_GAP),
        BOTTOM_PANEL_CELL_WIDTH,
        BOTTOM_PANEL_CELL_HEIGHT
    )


BUTTON_CLOCK: tuple = bottom_panel_cell(0, 0)
BUTTON_BIOMET: tuple = bottom_panel_cell(1, 0)
BUTTON_CAMERA: tuple = bottom_panel_cell(2, 0)
MODE_BUTTONS: tuple[tuple, ...] = (
    BUTTON_CLOCK,
    BUTTON_BIOMET,
    BUTTON_CAMERA,
)

DATE_TEXT_SIZE: float = 1.0
DATE_TEXT_COLOR: int = COLOR_WHITE
DATE_TEXT_X: int = DASHBOARD_PADDING
DATE_TEXT_Y: int = DASHBOARD_PADDING

DIGITAL_CLOCK_TEXT_SIZE: float = 5.0
DIGITAL_CLOCK_SECONDS_TEXT_SIZE: float = 2.0
DIGITAL_CLOCK_COLOR: int = COLOR_WHITE
DIGITAL_CLOCK_SECONDS_COLOR: int = 0xAAAAAA # light gray
DIGITAL_CLOCK_COLON_GAP: int = 4
CLOCK_AREA_CENTER_X: int = display.WIDTH//2
CLOCK_AREA_CENTER_Y: int = (BOTTOM_PANEL_Y - DASHBOARD_PADDING)//2 + 8
DIGITAL_CLOCK_TEXT_X: int = CLOCK_AREA_CENTER_X
DIGITAL_CLOCK_TEXT_Y: int = CLOCK_AREA_CENTER_Y
DIGITAL_CLOCK_SECONDS_TEXT_X: int = CLOCK_AREA_CENTER_X + 90
DIGITAL_CLOCK_SECONDS_TEXT_Y: int = CLOCK_AREA_CENTER_Y + 10


_previous_second: int = -1

# TODO: implement rest of the features


def on_input_update(topic: str, message: bytes):
    display.clear_screen()
    display.draw_text(message.decode('utf-8'))


def initialize():
    global _previous_second

    display.use_canvas()

    _previous_second = -1

    mqtt.register_handler(DASHBOARD__MQTT_INPUT_TOPIC, on_input_update)
    mqtt.subscribe(DASHBOARD__MQTT_INPUT_TOPIC)

    print("[DASH] initialized.")


def deinitialize():
    display.clear_canvas()
    display.flush_canvas()
    display.use_display()

    mqtt.unsubscribe(DASHBOARD__MQTT_INPUT_TOPIC)

    print("[DASH] deinitialized.")


def draw_digital_clock():
    hours, minutes, seconds = localtime.hour(), localtime.minute(), localtime.second()

    display.set_text_color(DIGITAL_CLOCK_COLOR)
    display.set_text_size(DIGITAL_CLOCK_TEXT_SIZE)
    display.draw_text(":", x=DIGITAL_CLOCK_TEXT_X, y=DIGITAL_CLOCK_TEXT_Y, anchor=display.MIDDLE_CENTER)
    display.draw_text(f"{hours:02}", x=DIGITAL_CLOCK_TEXT_X - DIGITAL_CLOCK_COLON_GAP, y=DIGITAL_CLOCK_TEXT_Y, anchor=display.MIDDLE_RIGHT)
    display.draw_text(f"{minutes:02}", x=DIGITAL_CLOCK_TEXT_X + DIGITAL_CLOCK_COLON_GAP, y=DIGITAL_CLOCK_TEXT_Y, anchor=display.MIDDLE_LEFT)


    display.draw_text( # smaller seconds on the right
        f"{seconds:02}",
        x=DIGITAL_CLOCK_SECONDS_TEXT_X,
        y=DIGITAL_CLOCK_SECONDS_TEXT_Y,
        size=DIGITAL_CLOCK_SECONDS_TEXT_SIZE,
        anchor=display.MIDDLE_CENTER,
        color=DIGITAL_CLOCK_SECONDS_COLOR
    )


def draw_bottom_buttons():
    ui.draw_button(BUTTON_CLOCK, label="CLK")
    ui.draw_button(BUTTON_BIOMET, label="BIO")
    ui.draw_button(BUTTON_CAMERA, label="CAM")


def handle_touch():
    if not touch.is_pressed() or not touch.was_pressed():
        return

    x, y = touch.position()
    touched_button_index: int = ui.is_inside_which(x, y, list(MODE_BUTTONS))
    if touched_button_index == 0:
        router.request_module_switch("clock")
    elif touched_button_index == 1:
        router.request_module_switch("biomet")
    elif touched_button_index == 2:
        router.request_module_switch("live_camera")


def update():
    global _previous_second
    handle_touch()

    current_second: int = localtime.second()

    if _previous_second != current_second:
        _previous_second = current_second

        # redraw only if second changed
        display.clear_canvas()

        draw_digital_clock()
        draw_bottom_buttons()

        display.flush_canvas()