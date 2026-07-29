import mqtt
import display
from config import *


# TODO: implement a proper dashboard


def _on_input_update(topic: str, message: str):
    display.clear_screen()
    display.show_text(message)


def initialize():
    # TODO: register_handler will be called multiple times if the module is switched back and forth
    # TODO: add unregister_handler ? or another idea
    mqtt.register_handler(DASHBOARD__MQTT_INPUT_TOPIC, _on_input_update)
    mqtt.subscribe(DASHBOARD__MQTT_INPUT_TOPIC)


def deinitialize():
    mqtt.unsubscribe(DASHBOARD__MQTT_INPUT_TOPIC)


def update():
    pass