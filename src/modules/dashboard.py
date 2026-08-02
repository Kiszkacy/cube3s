import time

import display
import mqtt
from config import *


DASHBOARD_PADDING: int = 8


DATE_TEXT_SIZE: float = 1.0
DATE_TEXT_COLOR: int = 0xFFFFFF # white
DATE_TEXT_X: int = DASHBOARD_PADDING
DATE_TEXT_Y: int = DASHBOARD_PADDING


DIGITAL_CLOCK_TEXT_SIZE: float = 5.0
DIGITAL_CLOCK_SECONDS_TEXT_SIZE: float = 2.0
DIGITAL_CLOCK_COLOR: int = 0xFFFFFF # white
DIGITAL_CLOCK_SECONDS_COLOR: int = 0xAAAAAA # light gray
DIGITAL_CLOCK_COLON_GAP: int = 2
DIGITAL_CLOCK_TEXT_X: int = DASHBOARD_PADDING + DIGITAL_CLOCK_COLON_GAP
DIGITAL_CLOCK_TEXT_Y: int = DASHBOARD_PADDING + 32 # display under DATE_TEXT
DIGITAL_CLOCK_SECONDS_TEXT_X: int = DASHBOARD_PADDING + DIGITAL_CLOCK_TEXT_X + 68
DIGITAL_CLOCK_SECONDS_TEXT_Y: int = DASHBOARD_PADDING + DIGITAL_CLOCK_TEXT_Y + 8 + 2


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
    now: time.struct_time = time.localtime(time.time() + UTC_OFFSET*3600)
    hours, minutes, seconds = now[3], now[4], now[5]

    display.set_text_color(DIGITAL_CLOCK_COLOR)
    display.set_text_size(DIGITAL_CLOCK_TEXT_SIZE)
    display.draw_text(":", x=DIGITAL_CLOCK_TEXT_X, y=DIGITAL_CLOCK_TEXT_Y, anchor="middle-center")
    display.draw_text(f"{hours:02}", x=DIGITAL_CLOCK_TEXT_X - DIGITAL_CLOCK_COLON_GAP, y=DIGITAL_CLOCK_TEXT_Y, anchor="middle-right")
    display.draw_text(f"{minutes:02}", x=DIGITAL_CLOCK_TEXT_X + DIGITAL_CLOCK_COLON_GAP, y=DIGITAL_CLOCK_TEXT_Y, anchor="middle-left")


    display.draw_text( # smaller seconds on the right
        f"{seconds:02}",
        x=DIGITAL_CLOCK_SECONDS_TEXT_X,
        y=DIGITAL_CLOCK_SECONDS_TEXT_Y,
        size=DIGITAL_CLOCK_SECONDS_TEXT_SIZE,
        anchor="middle-center",
        color=DIGITAL_CLOCK_SECONDS_COLOR
    )


def update():
    global _previous_second
    current_second: int = time.localtime()[5]

    if _previous_second != current_second:
        _previous_second = current_second

        # redraw only if second changed
        display.clear_canvas()

        draw_digital_clock()

        display.flush_canvas()