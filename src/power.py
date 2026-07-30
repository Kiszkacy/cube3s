import M5 # type: ignore


# typical usb voltage is at 5V
USB_CONNECTED_THRESHOLD: int = 4000 # millivolts


_power = M5.Power


def battery_level() -> int: # 0 - 100
    return _power.getBatteryLevel()


def is_charging() -> bool:
    return _power.isCharging()


def battery_voltage() -> int: # millivolts
    return _power.getBatteryVoltage()


def battery_current() -> float: # milliamps (negative while discharging)
    return _power.getBatteryCurrent()


def vbus_voltage() -> int: # millivolts
    return _power.getVBUSVoltage()


def is_usb_connected() -> bool:
    return _power.getVBUSVoltage() > USB_CONNECTED_THRESHOLD


def set_led(on: bool): # bottom green LED
    _power.setLed(255 if on else 0)
