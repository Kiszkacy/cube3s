import mqtt
import display
from config import *


def _on_input_update(topic: str, message: str):
    display.show_text(message)


def initialize():
    mqtt.register_handler(MQTT__INPUT_TOPIC, _on_input_update)
    mqtt.subscribe(MQTT__INPUT_TOPIC)

