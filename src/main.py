import M5 # type: ignore

# IMPORTANT: has to run before every other import
# so any global variables in the other modules that use M5 are initialized correctly
M5.begin()

import gc
import time

import router
import localtime
import mqtt
import power
import touch
import version
import wifi
import biomet, clock, dashboard, live_camera
from config import MQTT__MODULE_SWITCH_TOPIC

# TODO: cleanup variables and functions with and without _ to properly signal which ones are internal use only
# TODO: cleanup config.py, in there should only be user secret settings like passwords, not module-specific constants
# TODO: ideally get rid of any string comparisons even inside dict keys

LOOP_INTERVAL_MS: int = 50
LOOP_ERROR_DELAY_MS: int = 800

DEBUG__PRINT_MEMORY_STATUS: bool = False
DEBUG__MEMORY_STATUS_INTERVAL_MS: int = 10000

# module switching logic
MODULES: dict = {
    "biomet": biomet,
    "clock": clock,
    "dashboard": dashboard,
    "live_camera": live_camera,
}

# TODO: implement helper time module and daily reset logic

_current_module: str | None = "dashboard"

_next_memory_status_timestamp: int = 0


def print_memory_status_if_needed():
    global _next_memory_status_timestamp
    if not DEBUG__PRINT_MEMORY_STATUS:
        return
    if time.ticks_diff(time.ticks_ms(), _next_memory_status_timestamp) < 0:
        return
    _next_memory_status_timestamp = time.ticks_add(time.ticks_ms(), DEBUG__MEMORY_STATUS_INTERVAL_MS)

    used: int = gc.mem_alloc()
    free: int = gc.mem_free()
    total: int = used + free
    print(f"[MAIN.MEMORY] {used//1024}kb used, {free//1024}kb free, {total//1024}kb total ({used*100//total}% used).")


def on_module_switch(topic: str, message: bytes):
    # IMPORTANT: -- according to LLM --
    # this runs inside mqtt.check_if_any_message(), so it must not touch the socket itself.
    # initialize()/deinitialize() call subscribe()/unsubscribe(), which would re-enter the blocking
    # receive loop and can either hang the main loop or trip its packet id assert
    # TODO: this could crash if message was not a string
    module_name: str = message.decode('utf-8')
    if module_name not in MODULES:
        print(f"[MAIN.ROUTER] received unknown module switch request: '{module_name}'.")
        return

    router.request_module_switch(module_name)


def apply_pending_module_switch():
    global _current_module
    target: str | None = router.consume_pending_module_switch()
    if target is None:
        return

    if target not in MODULES:
        print(f"[MAIN.ROUTER] ignoring unknown module switch request: '{target}'.")
        return

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
        # IMPORTANT: sampled once per iteration, every module reads the sampled values instead of polling on its own
        localtime.update()
        touch.update()
        power.update()

        wifi.check_connection_reconnect_if_needed()
        mqtt.check_connection_reconnect_if_needed()
        mqtt.check_if_any_message()
        mqtt.ping_if_needed()
        apply_pending_module_switch()

        if _current_module:
            MODULES[_current_module].update()

        print_memory_status_if_needed()
    except Exception as e:
        print(f"[MAIN] unhandled error in main loop: '{e}'.")
        time.sleep_ms(LOOP_ERROR_DELAY_MS)

    time.sleep_ms(LOOP_INTERVAL_MS)
