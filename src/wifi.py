import time

import network

from config import *

TIMEOUT: int = 10


def connect():
    wlan: network.WLAN = network.WLAN(network.STA_IF)
    wlan.active(True)

    if wlan.isconnected():
        print(f"[WIFI] already connected.")
        return

    wlan.connect(WIFI__SSID, WIFI__PASSWORD)
    counter: int = TIMEOUT
    while counter > 0 and not wlan.isconnected():
        time.sleep(1)
        counter -= 1
        print(f"[WIFI] connecting...")

    if wlan.isconnected():
        my_ip: str = wlan.ifconfig()[0]
        print(f"[WIFI] successfully connected as {my_ip}.")
        return
    else:
        print(f"[WIFI] failed to connect.")


def disconnect():
    wlan: network.WLAN = network.WLAN(network.STA_IF)
    if wlan.isconnected():
        wlan.disconnect()
    wlan.active(False)


def is_connected() -> bool:
    wlan: network.WLAN = network.WLAN(network.STA_IF)
    return wlan.isconnected()
