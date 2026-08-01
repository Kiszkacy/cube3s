import mqtt
import display
from config import *


# TODO: implement a proper dashboard


def on_input_update(topic: str, message: bytes):
    display.clear_screen()
    display.draw_text(message.decode('utf-8'))


def initialize():
    # TODO: register_handler will be called multiple times if the module is switched back and forth
    # TODO: add unregister_handler ? or another idea
    mqtt.register_handler(DASHBOARD__MQTT_INPUT_TOPIC, on_input_update)
    mqtt.subscribe(DASHBOARD__MQTT_INPUT_TOPIC)

    print("[DASH] initialized.")


def deinitialize():
    mqtt.unsubscribe(DASHBOARD__MQTT_INPUT_TOPIC)

    print("[DASH] deinitialized.")


def update():
    pass