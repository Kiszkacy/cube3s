import mqtt
import display
import time
from config import *


# TODO: implement day switch buttons
# TODO: add date display ?
current_day_offset: int = 0 # -1 = yesterday, 0 = today, 1 = tomorrow


def on_image_received(topic: str, message: bytes):
    print(f"[BIOMET] received biomet.")

    display.clear_screen()
    display.draw_jpg_bytes(message, x=0, y=0)

    # TODO: draw date

    display.flush_canvas()
    # TODO: gc.collect() call after drawing ?


def get_date_as_string(day_offset: int = 0) -> str:
    target_seconds: int = time.time() + (UTC_OFFSET * 3600) + (day_offset * 86400)
    time_: time.struct_time = time.localtime(target_seconds)
    return "{:04d}-{:02d}-{:02d}".format(time_[0], time_[1], time_[2])


def request_biomet(day_offset: int = 0):
    global current_day_offset
    current_day_offset = day_offset

    command: str = f"GET_BIOMET:{get_date_as_string(day_offset)}"

    print(f"[BIOMET] requesting biomet...")
    mqtt.send_message(MQTT__WORKER_COMMAND_TOPIC, command)


def initialize():
    display.use_canvas()

    mqtt.register_handler(BIOMET__MQTT_IMAGE_TOPIC, on_image_received)
    mqtt.subscribe(BIOMET__MQTT_IMAGE_TOPIC)

    request_biomet(current_day_offset) # should remember last day that user looked at

    print("[BIOMET] initialized.")


def deinitialize():
    display.clear_canvas()
    display.flush_canvas()
    display.use_display()

    mqtt.unsubscribe(BIOMET__MQTT_IMAGE_TOPIC)

    print("[BIOMET] deinitialized.")


def update():
    pass