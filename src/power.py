import time

import M5 # type: ignore

# IMPORTANT: every getter here returns the value sampled by update(), a __RS variant reads the value immediately

# typical usb voltage is at 5V
USB_CONNECTED_THRESHOLD: int = 4000 # millivolts
BATTERY_PRESENT_THRESHOLD: int = 2000 # millivolts
SAMPLE_INTERVAL_MS: int = 60000 # 60 seconds


_power = M5.Power

_next_sample_timestamp: int = 0
_battery_level: int = 0
_battery_voltage: int = 0
_battery_current: float = 0.0
_is_charging: bool = False
_vbus_voltage: int = 0


def resample():
    global _next_sample_timestamp, _battery_level, _battery_voltage, _battery_current, _is_charging, _vbus_voltage
    _next_sample_timestamp = time.ticks_add(time.ticks_ms(), SAMPLE_INTERVAL_MS)

    _battery_level = _power.getBatteryLevel()
    _battery_voltage = _power.getBatteryVoltage()
    _battery_current = _power.getBatteryCurrent()
    _is_charging = _power.isCharging()
    _vbus_voltage = _power.getVBUSVoltage()


def update(): # IMPORTANT: has to be called once per main loop iteration, before the running module updates
    if time.ticks_diff(time.ticks_ms(), _next_sample_timestamp) < 0:
        return
    resample()


def battery_level() -> int: # 0 - 100
    return _battery_level


def battery_level__RS() -> int:
    global _battery_level
    _battery_level = _power.getBatteryLevel()
    return _battery_level


def battery_voltage() -> int: # millivolts
    return _battery_voltage


def battery_voltage__RS() -> int:
    global _battery_voltage
    _battery_voltage = _power.getBatteryVoltage()
    return _battery_voltage


def battery_current() -> float: # milliamps (negative while discharging)
    return _battery_current


def battery_current__RS() -> float:
    global _battery_current
    _battery_current = _power.getBatteryCurrent()
    return _battery_current


def is_charging() -> bool:
    return _is_charging


def is_charging__RS() -> bool:
    global _is_charging
    _is_charging = _power.isCharging()
    return _is_charging


def vbus_voltage() -> int: # millivolts
    return _vbus_voltage


def vbus_voltage__RS() -> int:
    global _vbus_voltage
    _vbus_voltage = _power.getVBUSVoltage()
    return _vbus_voltage


def is_usb_connected() -> bool:
    return _vbus_voltage > USB_CONNECTED_THRESHOLD


def is_usb_connected__RS() -> bool:
    return vbus_voltage__RS() > USB_CONNECTED_THRESHOLD


def is_battery_present() -> bool: # false while the device runs on usb only with the battery switched off
    return _battery_voltage > BATTERY_PRESENT_THRESHOLD


def is_battery_present__RS() -> bool:
    return battery_voltage__RS() > BATTERY_PRESENT_THRESHOLD


def set_led(on: bool): # bottom green LED
    _power.setLed(255 if on else 0)
