import time

import M5  # type: ignore

import mqtt
import wifi
from modules import dashboard, clock
from config import *

# module switching logic
MODULES: dict = {
    "clock": clock,
    "input": dashboard,
}


_current_module: str | None = None


def on_module_switch(topic: str, message: str):
    global _current_module
    if message not in MODULES:
        print(f"[MAIN.ROUTER] received unknown module switch request: '{message}'.")
        return
    
    if _current_module is not None:
        MODULES[_current_module].deinitialize()
    
    _current_module = message
    new_target_module = MODULES[_current_module]
    new_target_module.initialize()
    print(f"[MAIN.ROUTER] switched to module: '{_current_module}'.")


M5.begin()

wifi.connect()

mqtt.initialize()
mqtt.connect()
mqtt.register_handler(MQTT__MODULE_SWITCH_TOPIC, on_module_switch)

print(f"[MAIN] starting main loop.")
while True:
    M5.update()
    mqtt.check_if_any_message()

    if _current_module:
        MODULES[_current_module].update()

    time.sleep_ms(50)
