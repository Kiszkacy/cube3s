import display
import localtime
import mqtt
import router
import time
import touch
import ui
import common
from config import BIOMET__MQTT_IMAGE_RECEIVE_TOPIC, MQTT__WORKER_TOPIC, BIOMET__MQTT_MEDICAL_IMAGE_REQUEST_WORKER_TOPIC_SUFFIX, BIOMET__MQTT_PERSONAL_IMAGE_REQUEST_WORKER_TOPIC_SUFFIX, BIOMET__MQTT_RATING_RECEIVE_TOPIC, BIOMET__MQTT_RATING_REQUEST_WORKER_TOPIC_SUFFIX, BIOMET__MQTT_RATING_SEND_WORKER_TOPIC_SUFFIX


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

BACK_TO_DASHBOARD_BUTTON: tuple = ui.rect(
    ui.SCREEN_PADDING,
    ui.SCREEN_PADDING,
    44,
    36
)
BACK_TO_DASHBOARD_BUTTON_FILL_COLOR: int = 0x400000 # dark red
BACK_TO_DASHBOARD_BUTTON_BORDER_COLOR: int = ui.COLOR_WHITE

RATING_DIALOG_BUTTON: tuple = ui.rect(
    display.WIDTH - 44 - ui.SCREEN_PADDING,
    ui.SCREEN_PADDING,
    44,
    36
)
RATING_DIALOG_BUTTON_FILL_COLOR: int = 0x004000 # dark green
RATING_DIALOG_BUTTON_BORDER_COLOR: int = ui.COLOR_WHITE

RATING_DIALOG: tuple = ui.rect_around(
    display.WIDTH // 2,
    display.HEIGHT // 2,
    272,
    116
)
RATING_DIALOG_FILL_COLOR: int = 0x101820 # very dark blue
RATING_DIALOG_BORDER_COLOR: int = ui.COLOR_WHITE
RATING_DIALOG_TEXT_COLOR: int = ui.COLOR_WHITE
RATING_DIALOG_TEXT_SIZE: float = 2.0

RATING_BUTTON_WIDTH: int = 44
RATING_BUTTON_HEIGHT: int = 36
RATING_BUTTON_GAP: int = 8
RATING_BUTTONS_Y: int = RATING_DIALOG[1] + 64
RATING_BUTTONS_START_X: int = (display.WIDTH - (5 * RATING_BUTTON_WIDTH + 4 * RATING_BUTTON_GAP)) // 2

RATING_1_BUTTON: tuple = ui.rect(
    RATING_BUTTONS_START_X + 0 * (RATING_BUTTON_WIDTH + RATING_BUTTON_GAP),
    RATING_BUTTONS_Y,
    RATING_BUTTON_WIDTH,
    RATING_BUTTON_HEIGHT
)

RATING_2_BUTTON: tuple = ui.rect(
    RATING_BUTTONS_START_X + 1 * (RATING_BUTTON_WIDTH + RATING_BUTTON_GAP),
    RATING_BUTTONS_Y,
    RATING_BUTTON_WIDTH,
    RATING_BUTTON_HEIGHT
)

RATING_3_BUTTON: tuple = ui.rect(
    RATING_BUTTONS_START_X + 2 * (RATING_BUTTON_WIDTH + RATING_BUTTON_GAP),
    RATING_BUTTONS_Y,
    RATING_BUTTON_WIDTH,
    RATING_BUTTON_HEIGHT
)

RATING_4_BUTTON: tuple = ui.rect(
    RATING_BUTTONS_START_X + 3 * (RATING_BUTTON_WIDTH + RATING_BUTTON_GAP),
    RATING_BUTTONS_Y,
    RATING_BUTTON_WIDTH,
    RATING_BUTTON_HEIGHT
)

RATING_5_BUTTON: tuple = ui.rect(
    RATING_BUTTONS_START_X + 4 * (RATING_BUTTON_WIDTH + RATING_BUTTON_GAP),
    RATING_BUTTONS_Y,
    RATING_BUTTON_WIDTH,
    RATING_BUTTON_HEIGHT
)

MODE_SWITCH_BUTTON_FILL_COLOR: int = 0x004040 # dark cyan
MODE_SWITCH_BUTTON_BORDER_COLOR: int = ui.COLOR_WHITE
BUTTON_TEXT_SIZE: float = 2.0
BUTTON_TEXT_COLOR: int = ui.COLOR_WHITE

# TODO: move this to ui ?
BUTTON_DISABLED_FILL_COLOR: int = 0x1a1a1a # very dark gray
BUTTON_DISABLED_BORDER_COLOR: int = 0x333333 # dark gray
BUTTON_DISABLED_TEXT_COLOR: int = 0x666666 # dim gray
RATING_SELECTED_BORDER_COLOR: int = 0xFF0000 # bright red
BUTTONS: tuple[tuple, ...] = [
    MODE_SWITCH_BUTTON,
    NEXT_DAY_SWITCH_BUTTON,
    PREV_DAY_SWITCH_BUTTON,
    BACK_TO_DASHBOARD_BUTTON,
    RATING_DIALOG_BUTTON,
]
BUTTONS_VISIBLE_WHILE_RANKING_DIALOG_IS_VISIBLE: tuple[tuple, ...] = [
    RATING_1_BUTTON,
    RATING_2_BUTTON,
    RATING_3_BUTTON,
    RATING_4_BUTTON,
    RATING_5_BUTTON,
    BACK_TO_DASHBOARD_BUTTON,
    RATING_DIALOG_BUTTON,
]

BIOMET_REQUEST_TIMEOUT_MS: int = 3000


_mode: int = 0 # 0 => medical, 1 => personal
_ranking_dialog_visible: bool = False
_needs_redraw: bool = False
_selected_rating: int = -1 # -1 = no rating, 1-5 = user's rating choice
_last_biomet_request_timestamp: int = 0 # for timeout detection
current_day_offset: int = 0 # -1 = yesterday, 0 = today, 1 = tomorrow
_image_bytes: bytes | None = None


def on_rating_received(topic: str, message: bytes):
    global _selected_rating
    try:
        rating: int = int(message.decode('utf-8'))
        if -1 <= rating <= 5:
            _selected_rating = rating
            print(f"[BIOMET] received rating for current day: {rating}")
        else:
            print(f"[BIOMET] invalid rating value: {rating}")
    except ValueError:
        print(f"[BIOMET] failed to parse rating: {message.decode()}")


def on_image_received(topic: str, message: bytes):
    global _image_bytes, _needs_redraw

    if message.startswith(b"ERROR:"):
        print(f"[BIOMET] Worker failed to provide image: {message.decode()}")
        # TODO: error display flag
        return

    print(f"[BIOMET] received biomet image ({len(message)} bytes).")
    _image_bytes = message
    _needs_redraw = True


def request_medical_biomet(day_offset: int = 0):
    global _last_biomet_request_timestamp
    _last_biomet_request_timestamp = time.ticks_ms()
    command: str = f"{day_offset}"
    print(f"[BIOMET] requesting medical biomet...")
    mqtt.send_message(f"{MQTT__WORKER_TOPIC}{BIOMET__MQTT_MEDICAL_IMAGE_REQUEST_WORKER_TOPIC_SUFFIX}", command)


def request_personal_biomet(day_offset: int = 0):
    global _last_biomet_request_timestamp
    _last_biomet_request_timestamp = time.ticks_ms()
    command: str = f"{day_offset}"
    print(f"[BIOMET] requesting personal biomet...")
    mqtt.send_message(f"{MQTT__WORKER_TOPIC}{BIOMET__MQTT_PERSONAL_IMAGE_REQUEST_WORKER_TOPIC_SUFFIX}", command)


def request_biomet(day_offset: int = 0):
    if _mode == 0:
        request_medical_biomet(day_offset)
    else:
        request_personal_biomet(day_offset)


def initialize():
    global _needs_redraw, _selected_rating
    display.use_canvas()

    mqtt.register_handler(BIOMET__MQTT_IMAGE_RECEIVE_TOPIC, on_image_received)
    mqtt.subscribe(BIOMET__MQTT_IMAGE_RECEIVE_TOPIC)

    mqtt.register_handler(BIOMET__MQTT_RATING_RECEIVE_TOPIC, on_rating_received)
    mqtt.subscribe(BIOMET__MQTT_RATING_RECEIVE_TOPIC)

    _needs_redraw = True
    _selected_rating = -1
    request_biomet(current_day_offset) # should remember last day and mode that user looked at
    mqtt.send_message(f"{MQTT__WORKER_TOPIC}{BIOMET__MQTT_RATING_REQUEST_WORKER_TOPIC_SUFFIX}", f"{current_day_offset}")

    print("[BIOMET] initialized.")


def deinitialize():
    display.clear_canvas()
    display.flush_canvas()
    display.use_display()

    mqtt.unsubscribe(BIOMET__MQTT_IMAGE_RECEIVE_TOPIC)
    mqtt.unsubscribe(BIOMET__MQTT_RATING_RECEIVE_TOPIC)

    print("[BIOMET] deinitialized.")


def draw_received_image():
    display.draw_jpg_bytes(_image_bytes, x=0, y=0)


def draw_buttons():
    ui.draw_button(
        BACK_TO_DASHBOARD_BUTTON,
        label="BCK",
        fill_color=BACK_TO_DASHBOARD_BUTTON_FILL_COLOR,
        border_color=BACK_TO_DASHBOARD_BUTTON_BORDER_COLOR,
        text_color=BUTTON_TEXT_COLOR,
        text_size=BUTTON_TEXT_SIZE
    )

    disabled: bool = _ranking_dialog_visible
    ui.draw_button(
        MODE_SWITCH_BUTTON,
        label="MED" if _mode == 0 else "DIG",
        fill_color=BUTTON_DISABLED_FILL_COLOR if disabled else MODE_SWITCH_BUTTON_FILL_COLOR,
        border_color=BUTTON_DISABLED_BORDER_COLOR if disabled else MODE_SWITCH_BUTTON_BORDER_COLOR,
        text_color=BUTTON_DISABLED_TEXT_COLOR if disabled else BUTTON_TEXT_COLOR,
        text_size=BUTTON_TEXT_SIZE
    )

    disabled = _ranking_dialog_visible or current_day_offset >= 6
    ui.draw_button(
        NEXT_DAY_SWITCH_BUTTON,
        label=">",
        fill_color=BUTTON_DISABLED_FILL_COLOR if disabled else MODE_SWITCH_BUTTON_FILL_COLOR,
        border_color=BUTTON_DISABLED_BORDER_COLOR if disabled else MODE_SWITCH_BUTTON_FILL_COLOR,
        text_color=BUTTON_DISABLED_TEXT_COLOR if disabled else BUTTON_TEXT_COLOR,
        text_size=BUTTON_TEXT_SIZE
    )

    disabled = _ranking_dialog_visible or current_day_offset <= -6
    ui.draw_button(
        PREV_DAY_SWITCH_BUTTON,
        label="<",
        fill_color=BUTTON_DISABLED_FILL_COLOR if disabled else MODE_SWITCH_BUTTON_FILL_COLOR,
        border_color=BUTTON_DISABLED_BORDER_COLOR if disabled else MODE_SWITCH_BUTTON_FILL_COLOR,
        text_color=BUTTON_DISABLED_TEXT_COLOR if disabled else BUTTON_TEXT_COLOR,
        text_size=BUTTON_TEXT_SIZE
    )

    disabled = _ranking_dialog_visible or current_day_offset > 0
    ui.draw_button(
        RATING_DIALOG_BUTTON,
        label="RTN" if _ranking_dialog_visible else "SCR",
        fill_color=BUTTON_DISABLED_FILL_COLOR if disabled else RATING_DIALOG_BUTTON_FILL_COLOR,
        border_color=BUTTON_DISABLED_BORDER_COLOR if disabled else RATING_DIALOG_BUTTON_BORDER_COLOR,
        text_color=BUTTON_DISABLED_TEXT_COLOR if disabled else BUTTON_TEXT_COLOR,
        text_size=BUTTON_TEXT_SIZE
    )


def draw_rating_dialog():
    display.draw_round_rect(
        RATING_DIALOG[0],
        RATING_DIALOG[1],
        RATING_DIALOG[2],
        RATING_DIALOG[3],
        radius=10,
        color=RATING_DIALOG_FILL_COLOR,
        fill=True
    )
    display.draw_round_rect(
        RATING_DIALOG[0],
        RATING_DIALOG[1],
        RATING_DIALOG[2],
        RATING_DIALOG[3],
        radius=10,
        color=RATING_DIALOG_BORDER_COLOR
    )

    display.draw_text(
        "Rate how you feel today:",
        x=ui.center_x(RATING_DIALOG),
        y=RATING_DIALOG[1] + 20,
        size=RATING_DIALOG_TEXT_SIZE,
        anchor=display.TOP_CENTER,
        color=RATING_DIALOG_TEXT_COLOR,
        background_color=RATING_DIALOG_FILL_COLOR
    )

    for index, rating_button in enumerate([RATING_1_BUTTON, RATING_2_BUTTON, RATING_3_BUTTON, RATING_4_BUTTON, RATING_5_BUTTON]):
        is_selected: bool = (_selected_rating == (index + 1))
        ui.draw_button(
            rating_button,
            label=str(index+1),
            fill_color=RATING_DIALOG_BUTTON_FILL_COLOR,
            border_color=RATING_SELECTED_BORDER_COLOR if is_selected else RATING_DIALOG_BUTTON_BORDER_COLOR,
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
    global _mode, _ranking_dialog_visible, current_day_offset, _needs_redraw, _selected_rating
    if not touch.is_pressed():
        return

    x, y = touch.position()

    if not _ranking_dialog_visible:
        touched_button_index: int = ui.is_inside_which(x, y, BUTTONS)

        if touched_button_index == -1: # no button touched
            common.set_brightness_from_vertical_position(y)
        elif touched_button_index == 0 and touch.was_pressed(): # MODE_SWITCH_BUTTON
            _mode = 1 - _mode
            request_biomet(current_day_offset)
            mqtt.send_message(f"{MQTT__WORKER_TOPIC}{BIOMET__MQTT_RATING_REQUEST_WORKER_TOPIC_SUFFIX}", f"{current_day_offset}")
        elif touched_button_index == 1 and touch.was_pressed() and current_day_offset < 6: # NEXT_DAY_SWITCH_BUTTON
            current_day_offset += 1
            request_biomet(current_day_offset)
            mqtt.send_message(f"{MQTT__WORKER_TOPIC}{BIOMET__MQTT_RATING_REQUEST_WORKER_TOPIC_SUFFIX}", f"{current_day_offset}")
        elif touched_button_index == 2 and touch.was_pressed() and current_day_offset > -6: # PREV_DAY_SWITCH_BUTTON
            current_day_offset -= 1
            request_biomet(current_day_offset)
            mqtt.send_message(f"{MQTT__WORKER_TOPIC}{BIOMET__MQTT_RATING_REQUEST_WORKER_TOPIC_SUFFIX}", f"{current_day_offset}")
        elif touched_button_index == 3 and touch.was_pressed(): # BACK_TO_DASHBOARD_BUTTON
            router.request_module_switch("dashboard")
        elif touched_button_index == 4 and touch.was_pressed() and current_day_offset <= 0: # RATING_DIALOG_BUTTON
            _ranking_dialog_visible = True
            _needs_redraw = True
    else:
        touched_button_index: int = ui.is_inside_which(x, y, BUTTONS_VISIBLE_WHILE_RANKING_DIALOG_IS_VISIBLE)

        if touched_button_index == -1: # no button touched
            common.set_brightness_from_vertical_position(y)
        elif touched_button_index == 0 and touch.was_pressed(): # RATING_1_BUTTON
            mqtt.send_message(BIOMET__MQTT_RATING_SEND_WORKER_TOPIC_SUFFIX, f"1:{current_day_offset}")
            _selected_rating = 1
            _ranking_dialog_visible = False
            _needs_redraw = True
            print("[BIOMET] user rated 1.")
        elif touched_button_index == 1 and touch.was_pressed(): # RATING_2_BUTTON
            mqtt.send_message(BIOMET__MQTT_RATING_SEND_WORKER_TOPIC_SUFFIX, f"2:{current_day_offset}")
            _selected_rating = 2
            _ranking_dialog_visible = False
            _needs_redraw = True
            print("[BIOMET] user rated 2.")
        elif touched_button_index == 2 and touch.was_pressed(): # RATING_3_BUTTON
            mqtt.send_message(BIOMET__MQTT_RATING_SEND_WORKER_TOPIC_SUFFIX, f"3:{current_day_offset}")
            _selected_rating = 3
            _ranking_dialog_visible = False
            _needs_redraw = True
            print("[BIOMET] user rated 3.")
        elif touched_button_index == 3 and touch.was_pressed(): # RATING_4_BUTTON
            mqtt.send_message(BIOMET__MQTT_RATING_SEND_WORKER_TOPIC_SUFFIX, f"4:{current_day_offset}")
            _selected_rating = 4
            _ranking_dialog_visible = False
            _needs_redraw = True
            print("[BIOMET] user rated 4.")
        elif touched_button_index == 4 and touch.was_pressed(): # RATING_5_BUTTON
            mqtt.send_message(BIOMET__MQTT_RATING_SEND_WORKER_TOPIC_SUFFIX, f"5:{current_day_offset}")
            _selected_rating = 5
            _ranking_dialog_visible = False
            _needs_redraw = True
            print("[BIOMET] user rated 5.")
        elif touched_button_index == 5 and touch.was_pressed(): # BACK_TO_DASHBOARD_BUTTON
            router.request_module_switch("dashboard")
        elif touched_button_index == 6 and touch.was_pressed(): # RATING_DIALOG_BUTTON
            _ranking_dialog_visible = False
            _needs_redraw = True


def update():
    global _needs_redraw, _image_bytes, _selected_rating, current_day_offset

    handle_touch()

    # if during biomet fetch and didnt receive it yet
    show_data_missing: bool = False
    if _image_bytes is None and _last_biomet_request_timestamp > 0:
        time_since_request = time.ticks_diff(time.ticks_ms(), _last_biomet_request_timestamp)
        if time_since_request > BIOMET_REQUEST_TIMEOUT_MS:
            show_data_missing = True

    if (_needs_redraw or show_data_missing) and (_image_bytes is not None or show_data_missing):
        display.clear_canvas()
        
        if _image_bytes is not None:
            draw_received_image()
        else:
            display.draw_text(
                "Data missing",
                x=display.WIDTH // 2,
                y=display.HEIGHT // 2,
                size=3.0,
                anchor=display.MIDDLE_CENTER,
                color=ui.COLOR_WHITE
            )
        
        draw_buttons()
        draw_date()

        if _ranking_dialog_visible:
            draw_rating_dialog()

        display.flush_canvas()
        # TODO: gc.collect() call after drawing ?
        
        _needs_redraw = False
    