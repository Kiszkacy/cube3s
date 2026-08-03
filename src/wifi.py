import time

import network

from config import WIFI__PASSWORD, WIFI__SSID, WIFI__TIMEOUT_SECONDS


RETRY_INTERVAL_MS: int = 10000


_next_retry_timestamp: int = 0
_wlan: network.WLAN | None = None


def interface() -> network.WLAN: # cached, network.WLAN() allocates a new object on every call
    global _wlan
    if _wlan is None:
        _wlan = network.WLAN(network.STA_IF)
    return _wlan


def connect__B() -> bool:
    wlan: network.WLAN = interface()
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
    wlan: network.WLAN = interface()
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
    wlan: network.WLAN = interface()
    if wlan.isconnected():
        wlan.disconnect()
    wlan.active(False)


def is_connected() -> bool:
    return interface().isconnected()
