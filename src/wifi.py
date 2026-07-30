import time

import network

from config import *


RETRY_INTERVAL_MS: int = 10000


_next_retry_timestamp: int = 0


def connect__B() -> bool:
    wlan: network.WLAN = network.WLAN(network.STA_IF)
    wlan.active(True)

    if wlan.isconnected():
        my_ip: str = wlan.ipconfig('addr4')[0]
        print(f"[WIFI] already connected as {my_ip}.")
        return True

    wlan.connect(WIFI__SSID, WIFI__PASSWORD)
    counter: int = WIFI__TIMEOUT_SECONDS
    while counter > 0 and not wlan.isconnected():
        time.sleep(1)
        counter -= 1
        print(f"[WIFI] connecting...")

    if not wlan.isconnected():
        print("[WIFI] failed to connect.")
        return False

    my_ip: str = wlan.ipconfig('addr4')[0]
    print(f"[WIFI] successfully connected as {my_ip}.")
    return True


def check_connection_reconnect_if_needed():
    global _next_retry_timestamp
    wlan: network.WLAN = network.WLAN(network.STA_IF)
    if wlan.isconnected():
        return
    if time.ticks_diff(time.ticks_ms(), _next_retry_timestamp) < 0:
        return

    _next_retry_timestamp = time.ticks_add(time.ticks_ms(), RETRY_INTERVAL_MS)
    print("[WIFI] disconnected, retrying...")
    try:
        wlan.active(True)
        wlan.connect(WIFI__SSID, WIFI__PASSWORD)
    except OSError as e:
        print(f"[WIFI] retry failed: '{e}'.")


def disconnect():
    wlan: network.WLAN = network.WLAN(network.STA_IF)
    if wlan.isconnected():
        wlan.disconnect()
    wlan.active(False)


def is_connected() -> bool:
    wlan: network.WLAN = network.WLAN(network.STA_IF)
    return wlan.isconnected()
