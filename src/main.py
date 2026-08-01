import M5 # type: ignore

# IMPORTANT: has to run before every other import
# so any global variables in the other modules that use M5 are initialized correctly
M5.begin()

import time

import mqtt
import version
import wifi
from modules import clock, dashboard, live_camera
# TODO: cleanup config.py, in there should only be user secret settings like passwords, not module-specific constants
from config import *

LOOP_INTERVAL_MS: int = 50
LOOP_ERROR_DELAY_MS: int = 800

# module switching logic
MODULES: dict = {
    "clock": clock,
    "input": dashboard,
    "live_camera": live_camera
}

# TODO: implement helper time module and daily reset logic

_current_module: str | None = None
_pending_module: str | None = None


def on_module_switch(topic: str, message: bytes):
    # IMPORTANT: -- according to LLM --
    # this runs inside mqtt.check_if_any_message(), so it must not touch the socket itself.
    # initialize()/deinitialize() call subscribe()/unsubscribe(), which would re-enter the blocking
    # receive loop and can either hang the main loop or trip its packet id assert
    global _pending_module
    # TODO: this could crash if message was not a string
    module_name: str = message.decode('utf-8')
    if module_name not in MODULES:
        print(f"[MAIN.ROUTER] received unknown module switch request: '{module_name}'.")
        return

    _pending_module = module_name


def apply_pending_module_switch():
    global _current_module, _pending_module
    if _pending_module is None:
        return

    target: str = _pending_module
    _pending_module = None

    if target == _current_module:
        return

    if _current_module is not None:
        MODULES[_current_module].deinitialize()
        _current_module = None # until new module is initialized

    MODULES[target].initialize()
    _current_module = target
    print(f"[MAIN.ROUTER] switched to module: '{_current_module}'.")


print(f"[MAIN] cube3s v{version.VERSION}.")

wifi.connect__B()

mqtt.initialize()
mqtt.connect()
mqtt.register_handler(MQTT__MODULE_SWITCH_TOPIC, on_module_switch)
mqtt.subscribe(MQTT__MODULE_SWITCH_TOPIC)

print("[MAIN] starting main loop.")
# TODO: measure frame time and loop execution time
while True:
    try:
        M5.update()
        wifi.check_connection_reconnect_if_needed()
        mqtt.check_connection_reconnect_if_needed()
        mqtt.check_if_any_message()
        mqtt.ping_if_needed()
        apply_pending_module_switch()

        if _current_module:
            MODULES[_current_module].update()
    except Exception as e:
        print(f"[MAIN] unhandled error in main loop: '{e}'.")
        time.sleep_ms(LOOP_ERROR_DELAY_MS)

    time.sleep_ms(LOOP_INTERVAL_MS)
