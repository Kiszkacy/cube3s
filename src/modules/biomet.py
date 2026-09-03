import display
import localtime
import mqtt
import router
import time
import touch
import ui
import common
from config import BIOMET__MQTT_IMAGE_RECEIVE_TOPIC, MQTT__WORKER_TOPIC, BIOMET__MQTT_MEDICAL_IMAGE_REQUEST_WORKER_TOPIC_SUFFIX, BIOMET__MQTT_PERSONAL_IMAGE_REQUEST_WORKER_TOPIC_SUFFIX, BIOMET__MQTT_RATING_RECEIVE_TOPIC, BIOMET__MQTT_RATING_REQUEST_WORKER_TOPIC_SUFFIX, BIOMET__MQTT_RATING_SEND_WORKER_TOPIC_SUFFIX


SERVICES: tuple[str, ...] = ()


MODE_SWITCH_BUTTON: tuple = ui.rect(
    display.WIDTH - 44 - ui.SCREEN_PADDING,
    display.HEIGHT - 36 - ui.SCREEN_PADDING,
    44,
    36
)

NEXT_DAY_SWITCH_BUTTON: tuple = ui.rect(
    display.WIDTH - 24 - ui.SCREEN_PADDING,
    display.HEIGHT//2 - 96//2 - ui.SCREEN_PADDING//2,
    24,
    96
)

PREV_DAY_SWITCH_BUTTON: tuple = ui.rect(
    ui.SCREEN_PADDING,
    display.HEIGHT//2 - 96//2 - ui.SCREEN_PADDING//2,
    24,
    96
)

BACK_TO_DASHBOARD_BUTTON: tuple = ui.rect(
    ui.SCREEN_PADDING,
    ui.SCREEN_PADDING,
    44,
    36
)
BACK_TO_DASHBOARD_BUTTON_FILL_COLOR: int = 0x400000 # dark red
BACK_TO_DASHBOARD_BUTTON_BORDER_COLOR: int = ui.COLOR_WHITE

SCORE_DIALOG_BUTTON: tuple = ui.rect(
    display.WIDTH - 44 - ui.SCREEN_PADDING,
    ui.SCREEN_PADDING,
    44,
    36
)
SCORE_DIALOG_BUTTON_FILL_COLOR: int = 0x004000 # dark green
SCORE_DIALOG_BUTTON_BORDER_COLOR: int = ui.COLOR_WHITE
SCORE_DIALOG_BUTTON_EXIT_FILL_COLOR: int = 0x400000 # dark red
SCORE_DIALOG_BUTTON_EXIT_BORDER_COLOR: int = ui.COLOR_WHITE

SCORE_DIALOG: tuple = ui.rect_around(
    display.WIDTH // 2,
    display.HEIGHT // 2,
    272,
    116
)
SCORE_DIALOG_FILL_COLOR: int = 0x101820 # very dark blue
SCORE_DIALOG_BORDER_COLOR: int = ui.COLOR_WHITE
SCORE_DIALOG_TEXT_COLOR: int = ui.COLOR_WHITE
SCORE_DIALOG_TEXT_SIZE: float = 2.0

SCORE_BUTTON_WIDTH: int = 44
SCORE_BUTTON_HEIGHT: int = 36
SCORE_BUTTON_GAP: int = 8
SCORE_BUTTONS_Y: int = SCORE_DIALOG[1] + 64
SCORE_BUTTONS_START_X: int = (display.WIDTH - (5 * SCORE_BUTTON_WIDTH + 4 * SCORE_BUTTON_GAP)) // 2

SCORE_1_BUTTON: tuple = ui.rect(
    SCORE_BUTTONS_START_X + 0 * (SCORE_BUTTON_WIDTH + SCORE_BUTTON_GAP),
    SCORE_BUTTONS_Y,
    SCORE_BUTTON_WIDTH,
    SCORE_BUTTON_HEIGHT
)

SCORE_2_BUTTON: tuple = ui.rect(
    SCORE_BUTTONS_START_X + 1 * (SCORE_BUTTON_WIDTH + SCORE_BUTTON_GAP),
    SCORE_BUTTONS_Y,
    SCORE_BUTTON_WIDTH,
    SCORE_BUTTON_HEIGHT
)

SCORE_3_BUTTON: tuple = ui.rect(
    SCORE_BUTTONS_START_X + 2 * (SCORE_BUTTON_WIDTH + SCORE_BUTTON_GAP),
    SCORE_BUTTONS_Y,
    SCORE_BUTTON_WIDTH,
    SCORE_BUTTON_HEIGHT
)

SCORE_4_BUTTON: tuple = ui.rect(
    SCORE_BUTTONS_START_X + 3 * (SCORE_BUTTON_WIDTH + SCORE_BUTTON_GAP),
    SCORE_BUTTONS_Y,
    SCORE_BUTTON_WIDTH,
    SCORE_BUTTON_HEIGHT
)

SCORE_5_BUTTON: tuple = ui.rect(
    SCORE_BUTTONS_START_X + 4 * (SCORE_BUTTON_WIDTH + SCORE_BUTTON_GAP),
    SCORE_BUTTONS_Y,
    SCORE_BUTTON_WIDTH,
    SCORE_BUTTON_HEIGHT
)

BUTTON_FILL_COLOR: int = 0x004040 # dark cyan
BUTTON_BORDER_COLOR: int = ui.COLOR_WHITE
BUTTON_TEXT_SIZE: float = 2.0
BUTTON_TEXT_COLOR: int = ui.COLOR_WHITE

# TODO: move this to ui ?
BUTTON_DISABLED_FILL_COLOR: int = 0x1a1a1a # very dark gray
BUTTON_DISABLED_BORDER_COLOR: int = 0x333333 # dark gray
BUTTON_DISABLED_TEXT_COLOR: int = 0x666666 # dim gray
SCORE_SELECTED_BORDER_COLOR: int = 0xFF0000 # bright red
BUTTONS: tuple[tuple, ...] = (
    MODE_SWITCH_BUTTON,
    NEXT_DAY_SWITCH_BUTTON,
    PREV_DAY_SWITCH_BUTTON,
    BACK_TO_DASHBOARD_BUTTON,
    SCORE_DIALOG_BUTTON,
)
BUTTONS_VISIBLE_WHILE_SCORE_DIALOG_IS_VISIBLE: tuple[tuple, ...] = (
    SCORE_1_BUTTON,
    SCORE_2_BUTTON,
    SCORE_3_BUTTON,
    SCORE_4_BUTTON,
    SCORE_5_BUTTON,
    SCORE_DIALOG_BUTTON,
)

BIOMET_REQUEST_TIMEOUT_MS: int = 1500

IMAGE_STATE_NO_IMAGE: int = 0
IMAGE_STATE_WAITING: int = 1
IMAGE_STATE_MISSING: int = 2
IMAGE_STATE_READY: int = 3


_image_state: int = IMAGE_STATE_NO_IMAGE
_image_bytes: bytes | None = None

current_day_offset: int = 0 # -1 = yesterday, 0 = today, 1 = tomorrow
_mode: int = 0 # 0 => medical, 1 => personal
_selected_score: int = -1 # -1 = no score, 1-5 = user's score choice

_score_dialog_visible: bool = False
_needs_redraw: bool = False
_last_biomet_request_timestamp: int = -1 # for timeout detection


def on_score_received(topic: str, message: bytes):
    global _selected_score
    try:
        score: int = int(message.decode('utf-8'))
        if -1 <= score <= 5:
            _selected_score = score
            print(f"[BIOMET] received score for current day: {score}")
        else:
            print(f"[BIOMET] invalid score value: {score}")
    except ValueError:
        print(f"[BIOMET] failed to parse score: {message.decode()}")


def on_image_received(topic: str, message: bytes):
    global _image_bytes, _needs_redraw, _image_state, _last_biomet_request_timestamp

    _last_biomet_request_timestamp = -1
    _needs_redraw = True
    if message.startswith(b"ERROR:"):
        print(f"[BIOMET] Worker failed to provide image: {message.decode()}")
        _image_state = IMAGE_STATE_MISSING
        return

    print(f"[BIOMET] received biomet image ({len(message)} bytes).")
    _image_bytes = message
    _image_state = IMAGE_STATE_READY


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
    global _image_state
    _image_state = IMAGE_STATE_WAITING
    if _mode == 0:
        request_medical_biomet(day_offset)
    else:
        request_personal_biomet(day_offset)


def initialize():
    global _needs_redraw, _selected_score, _image_state, _image_bytes
    display.use_canvas()

    mqtt.register_handler(BIOMET__MQTT_IMAGE_RECEIVE_TOPIC, on_image_received)
    mqtt.subscribe(BIOMET__MQTT_IMAGE_RECEIVE_TOPIC)

    mqtt.register_handler(BIOMET__MQTT_RATING_RECEIVE_TOPIC, on_score_received)
    mqtt.subscribe(BIOMET__MQTT_RATING_RECEIVE_TOPIC)

    _needs_redraw = True
    _selected_score = -1
    _image_state = IMAGE_STATE_NO_IMAGE
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
    disabled: bool = _score_dialog_visible
    ui.draw_button(
        BACK_TO_DASHBOARD_BUTTON,
        label="BCK",
        fill_color=BUTTON_DISABLED_FILL_COLOR if disabled else BACK_TO_DASHBOARD_BUTTON_FILL_COLOR,
        border_color=BUTTON_DISABLED_BORDER_COLOR if disabled else BACK_TO_DASHBOARD_BUTTON_BORDER_COLOR,
        text_color=BUTTON_DISABLED_TEXT_COLOR if disabled else BUTTON_TEXT_COLOR,
        text_size=BUTTON_TEXT_SIZE
    )

    disabled = _score_dialog_visible
    ui.draw_button(
        MODE_SWITCH_BUTTON,
        label="CUS" if _mode == 0 else "MED",
        fill_color=BUTTON_DISABLED_FILL_COLOR if disabled else BUTTON_FILL_COLOR,
        border_color=BUTTON_DISABLED_BORDER_COLOR if disabled else BUTTON_BORDER_COLOR,
        text_color=BUTTON_DISABLED_TEXT_COLOR if disabled else BUTTON_TEXT_COLOR,
        text_size=BUTTON_TEXT_SIZE
    )

    disabled = _score_dialog_visible or current_day_offset >= 6 or _image_state == IMAGE_STATE_WAITING
    ui.draw_button(
        NEXT_DAY_SWITCH_BUTTON,
        label=">",
        fill_color=BUTTON_DISABLED_FILL_COLOR if disabled else BUTTON_FILL_COLOR,
        border_color=BUTTON_DISABLED_BORDER_COLOR if disabled else BUTTON_BORDER_COLOR,
        text_color=BUTTON_DISABLED_TEXT_COLOR if disabled else BUTTON_TEXT_COLOR,
        text_size=BUTTON_TEXT_SIZE
    )

    disabled = _score_dialog_visible or current_day_offset <= -6 or _image_state == IMAGE_STATE_WAITING
    ui.draw_button(
        PREV_DAY_SWITCH_BUTTON,
        label="<",
        fill_color=BUTTON_DISABLED_FILL_COLOR if disabled else BUTTON_FILL_COLOR,
        border_color=BUTTON_DISABLED_BORDER_COLOR if disabled else BUTTON_BORDER_COLOR,
        text_color=BUTTON_DISABLED_TEXT_COLOR if disabled else BUTTON_TEXT_COLOR,
        text_size=BUTTON_TEXT_SIZE
    )

    disabled = current_day_offset > 0
    in_exit_mode: bool = _score_dialog_visible
    ui.draw_button(
        SCORE_DIALOG_BUTTON,
        label="RTN" if _score_dialog_visible else "SCR",
        fill_color=BUTTON_DISABLED_FILL_COLOR if disabled else SCORE_DIALOG_BUTTON_EXIT_FILL_COLOR if in_exit_mode else SCORE_DIALOG_BUTTON_FILL_COLOR,
        border_color=BUTTON_DISABLED_BORDER_COLOR if disabled else SCORE_DIALOG_BUTTON_EXIT_BORDER_COLOR if in_exit_mode else SCORE_DIALOG_BUTTON_BORDER_COLOR,
        text_color=BUTTON_DISABLED_TEXT_COLOR if disabled else BUTTON_TEXT_COLOR,
        text_size=BUTTON_TEXT_SIZE
    )


def draw_score_dialog():
    display.draw_round_rect(
        SCORE_DIALOG[0],
        SCORE_DIALOG[1],
        SCORE_DIALOG[2],
        SCORE_DIALOG[3],
        radius=8,
        color=SCORE_DIALOG_FILL_COLOR,
        fill=True
    )
    display.draw_round_rect(
        SCORE_DIALOG[0],
        SCORE_DIALOG[1],
        SCORE_DIALOG[2],
        SCORE_DIALOG[3],
        radius=8,
        color=SCORE_DIALOG_BORDER_COLOR
    )

    display.draw_text(
        "Rate how you felt:",
        x=ui.center_x(SCORE_DIALOG),
        y=SCORE_DIALOG[1] + 20,
        size=SCORE_DIALOG_TEXT_SIZE,
        anchor=display.TOP_CENTER,
        color=SCORE_DIALOG_TEXT_COLOR,
        background_color=SCORE_DIALOG_FILL_COLOR
    )

    for index, score_button in enumerate([SCORE_1_BUTTON, SCORE_2_BUTTON, SCORE_3_BUTTON, SCORE_4_BUTTON, SCORE_5_BUTTON]):
        is_selected: bool = (_selected_score == (index + 1))
        ui.draw_button(
            score_button,
            label=str(index+1),
            fill_color=SCORE_DIALOG_BUTTON_FILL_COLOR,
            border_color=SCORE_SELECTED_BORDER_COLOR if is_selected else SCORE_DIALOG_BUTTON_BORDER_COLOR,
            text_color=BUTTON_TEXT_COLOR,
            text_size=BUTTON_TEXT_SIZE
        )


def draw_date():
    display.draw_text(
        localtime.date_string(current_day_offset),
        x=ui.SCREEN_PADDING,
        y=display.HEIGHT-ui.SCREEN_PADDING-16,
        size=2.0,
        anchor=display.TOP_LEFT,
        color=ui.COLOR_WHITE
    )


def handle_touch():
    global _mode, _score_dialog_visible, current_day_offset, _needs_redraw, _selected_score
    if not touch.is_pressed():
        return

    x, y = touch.position()

    if not _score_dialog_visible:
        touched_button_index: int = ui.is_inside_which(x, y, BUTTONS)

        if touched_button_index == -1: # no button touched
            common.set_brightness_from_vertical_position(y)
        elif touched_button_index == 0 and touch.was_pressed(): # MODE_SWITCH_BUTTON
            _mode = 1 - _mode
            request_biomet(current_day_offset)
            _needs_redraw = True
            mqtt.send_message(f"{MQTT__WORKER_TOPIC}{BIOMET__MQTT_RATING_REQUEST_WORKER_TOPIC_SUFFIX}", f"{current_day_offset}")
        elif touched_button_index == 1 and touch.was_pressed() and current_day_offset < 6 and _image_state != IMAGE_STATE_WAITING: # NEXT_DAY_SWITCH_BUTTON
            current_day_offset += 1
            request_biomet(current_day_offset)
            _needs_redraw = True
            mqtt.send_message(f"{MQTT__WORKER_TOPIC}{BIOMET__MQTT_RATING_REQUEST_WORKER_TOPIC_SUFFIX}", f"{current_day_offset}")
        elif touched_button_index == 2 and touch.was_pressed() and current_day_offset > -6 and _image_state != IMAGE_STATE_WAITING: # PREV_DAY_SWITCH_BUTTON
            current_day_offset -= 1
            request_biomet(current_day_offset)
            _needs_redraw = True
            mqtt.send_message(f"{MQTT__WORKER_TOPIC}{BIOMET__MQTT_RATING_REQUEST_WORKER_TOPIC_SUFFIX}", f"{current_day_offset}")
        elif touched_button_index == 3 and touch.was_pressed(): # BACK_TO_DASHBOARD_BUTTON
            router.request_module_switch("dashboard")
        elif touched_button_index == 4 and touch.was_pressed() and current_day_offset <= 0: # SCORE_DIALOG_BUTTON
            _score_dialog_visible = True
            _needs_redraw = True
    else:
        touched_button_index: int = ui.is_inside_which(x, y, BUTTONS_VISIBLE_WHILE_SCORE_DIALOG_IS_VISIBLE)

        if touched_button_index == -1: # no button touched
            common.set_brightness_from_vertical_position(y)
        elif touched_button_index == 0 and touch.was_pressed(): # SCORE_1_BUTTON
            mqtt.send_message(f"{MQTT__WORKER_TOPIC}{BIOMET__MQTT_RATING_SEND_WORKER_TOPIC_SUFFIX}", f"1:{current_day_offset}")
            _selected_score = 1
            _score_dialog_visible = False
            _needs_redraw = True
            print("[BIOMET] user rated 1.")
        elif touched_button_index == 1 and touch.was_pressed(): # SCORE_2_BUTTON
            mqtt.send_message(f"{MQTT__WORKER_TOPIC}{BIOMET__MQTT_RATING_SEND_WORKER_TOPIC_SUFFIX}", f"2:{current_day_offset}")
            _selected_score = 2
            _score_dialog_visible = False
            _needs_redraw = True
            print("[BIOMET] user rated 2.")
        elif touched_button_index == 2 and touch.was_pressed(): # SCORE_3_BUTTON
            mqtt.send_message(f"{MQTT__WORKER_TOPIC}{BIOMET__MQTT_RATING_SEND_WORKER_TOPIC_SUFFIX}", f"3:{current_day_offset}")
            _selected_score = 3
            _score_dialog_visible = False
            _needs_redraw = True
            print("[BIOMET] user rated 3.")
        elif touched_button_index == 3 and touch.was_pressed(): # SCORE_4_BUTTON
            mqtt.send_message(f"{MQTT__WORKER_TOPIC}{BIOMET__MQTT_RATING_SEND_WORKER_TOPIC_SUFFIX}", f"4:{current_day_offset}")
            _selected_score = 4
            _score_dialog_visible = False
            _needs_redraw = True
            print("[BIOMET] user rated 4.")
        elif touched_button_index == 4 and touch.was_pressed(): # SCORE_5_BUTTON
            mqtt.send_message(f"{MQTT__WORKER_TOPIC}{BIOMET__MQTT_RATING_SEND_WORKER_TOPIC_SUFFIX}", f"5:{current_day_offset}")
            _selected_score = 5
            _score_dialog_visible = False
            _needs_redraw = True
            print("[BIOMET] user rated 5.")
        elif touched_button_index == 5 and touch.was_pressed(): # SCORE_DIALOG_BUTTON
            _score_dialog_visible = False
            _needs_redraw = True


def update():
    global _needs_redraw, _image_bytes, _selected_score, current_day_offset, _image_state

    handle_touch()

    if _image_state == IMAGE_STATE_WAITING and _last_biomet_request_timestamp != -1:
        time_since_request: int = time.ticks_diff(time.ticks_ms(), _last_biomet_request_timestamp)
        if time_since_request > BIOMET_REQUEST_TIMEOUT_MS:
            _image_state = IMAGE_STATE_MISSING
            _needs_redraw = True

    if _needs_redraw:
        display.clear_canvas()

        if _image_state == IMAGE_STATE_MISSING:
            display.draw_text(
                "Data missing",
                x=display.WIDTH // 2,
                y=display.HEIGHT // 2,
                size=3.0,
                anchor=display.MIDDLE_CENTER,
                color=ui.COLOR_WHITE
            )
        elif _image_bytes is not None:
            draw_received_image()
        
        draw_buttons()
        draw_date()

        if _score_dialog_visible:
            draw_score_dialog()

        display.flush_canvas()
        # TODO: gc.collect() call after drawing ?
        
        _needs_redraw = False
    