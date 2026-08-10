import display
import localtime
import mqtt
import touch
import ui
import common
from config import BIOMET__MQTT_IMAGE_RECEIVE_TOPIC, MQTT__WORKER_TOPIC, BIOMET__MQTT_IMAGE_REQUEST_WORKER_TOPIC_SUFFIX

MODE_SWITCH_BUTTON: tuple = ui.rect(
    display.WIDTH - 44 - ui.SCREEN_PADDING,
    display.HEIGHT - 36 - ui.SCREEN_PADDING,
    44,
    36
)


NEXT_DAY_SWITCH_BUTTON: tuple = ui.rect(
    display.WIDTH - 24 - ui.SCREEN_PADDING,
    display.HEIGHT//2 - 72//2 - ui.SCREEN_PADDING//2,
    24,
    72
)

PREV_DAY_SWITCH_BUTTON: tuple = ui.rect(
    ui.SCREEN_PADDING,
    display.HEIGHT//2 - 72//2 - ui.SCREEN_PADDING//2,
    24,
    72
)

MODE_SWITCH_BUTTON_FILL_COLOR: int = 0x004040 # dark cyan
MODE_SWITCH_BUTTON_BORDER_COLOR: int = ui.COLOR_WHITE
BUTTON_TEXT_SIZE: float = 2.0
BUTTON_TEXT_COLOR: int = ui.COLOR_WHITE
BUTTONS: tuple[tuple, ...] = [
    MODE_SWITCH_BUTTON,
    NEXT_DAY_SWITCH_BUTTON,
    PREV_DAY_SWITCH_BUTTON,
]

_mode: int = 0 # 0 => medical, 1 => personal

# TODO: implement day switch buttons
# TODO: add date display ?
current_day_offset: int = 0 # -1 = yesterday, 0 = today, 1 = tomorrow

_image_bytes: bytes | None = None
_image_queued: bool = False


def on_image_received(topic: str, message: bytes):
    global _image_queued, _image_bytes

    if message.startswith(b"ERROR:"):
        print(f"[BIOMET] Worker failed to provide image: {message.decode()}")
        # TODO: error display flag
        return

    print(f"[BIOMET] received biomet image ({len(message)} bytes).")
    _image_bytes = message
    _image_queued = True


def request_biomet(day_offset: int = 0):
    global current_day_offset
    current_day_offset = day_offset

    command: str = f"{day_offset}"
    print(f"[BIOMET] requesting biomet...")
    mqtt.send_message(f"{MQTT__WORKER_TOPIC}{BIOMET__MQTT_IMAGE_REQUEST_WORKER_TOPIC_SUFFIX}", command)


def initialize():
    display.use_canvas()

    mqtt.register_handler(BIOMET__MQTT_IMAGE_RECEIVE_TOPIC, on_image_received)
    mqtt.subscribe(BIOMET__MQTT_IMAGE_RECEIVE_TOPIC)

    request_biomet(current_day_offset) # should remember last day that user looked at

    print("[BIOMET] initialized.")


def deinitialize():
    display.clear_canvas()
    display.flush_canvas()
    display.use_display()

    mqtt.unsubscribe(BIOMET__MQTT_IMAGE_RECEIVE_TOPIC)

    print("[BIOMET] deinitialized.")


def draw_received_image():
    display.draw_jpg_bytes(_image_bytes, x=0, y=0)


def draw_buttons():
    ui.draw_button(
        MODE_SWITCH_BUTTON,
        label="MED" if _mode == 0 else "DIG",
        fill_color=MODE_SWITCH_BUTTON_FILL_COLOR,
        border_color=MODE_SWITCH_BUTTON_FILL_COLOR,
        text_color=BUTTON_TEXT_COLOR,
        text_size=BUTTON_TEXT_SIZE
    )

    ui.draw_button(
        NEXT_DAY_SWITCH_BUTTON,
        label=">",
        fill_color=MODE_SWITCH_BUTTON_FILL_COLOR,
        border_color=MODE_SWITCH_BUTTON_FILL_COLOR,
        text_color=BUTTON_TEXT_COLOR,
        text_size=BUTTON_TEXT_SIZE
    )

    ui.draw_button(
        PREV_DAY_SWITCH_BUTTON,
        label="<",
        fill_color=MODE_SWITCH_BUTTON_FILL_COLOR,
        border_color=MODE_SWITCH_BUTTON_FILL_COLOR,
        text_color=BUTTON_TEXT_COLOR,
        text_size=BUTTON_TEXT_SIZE
    )


def draw_date():
    display.draw_text(
        f"{localtime.year()}.{localtime.month():02d}.{localtime.day():02d}",
        x=ui.SCREEN_PADDING,
        y=display.HEIGHT-ui.SCREEN_PADDING-16,
        size=2.0,
        anchor=display.TOP_LEFT,
        color=ui.COLOR_WHITE
    )


def handle_touch():
    if not touch.is_pressed():
        return

    x, y = touch.position()
    if ui.is_inside_which(x, y, BUTTONS) != -1:
        return

    common.set_brightness_from_vertical_position(y)


def update():
    global _image_queued

    handle_touch()

    if _image_queued and _image_bytes is not None:
        draw_received_image()
        draw_buttons()
        draw_date()

        # TODO: draw date

        display.flush_canvas()
        # TODO: gc.collect() call after drawing ?
        
        _image_queued = False
    