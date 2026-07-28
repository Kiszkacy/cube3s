import time

import M5  # type: ignore

import mqtt
import wifi
from modules import input_test

M5.begin()

wifi.connect()

mqtt.initialize()
mqtt.connect()

input_test.initialize()

while True:
    M5.update()
    mqtt.check_if_any_message()
    time.sleep_ms(50)
