import env
import localtime
import mqtt
from config import (
    SERVICE__HUMIDIFIER_HUMIDITY_MIN,
    SERVICE__HUMIDIFIER_HUMIDITY_MAX,
    SERVICE__HUMIDIFIER_DAY_START_HOUR,
    SERVICE__HUMIDIFIER_DAY_END_HOUR,
    SERVICE__HUMIDIFIER_POWER_TOPIC,
)


ON_MESSAGE: str = "ON"
OFF_MESSAGE: str = "OFF"

_last_sent_state: str | None = None


def _is_daytime() -> bool:
    hour: int = localtime.hour()
    return SERVICE__HUMIDIFIER_DAY_START_HOUR <= hour < SERVICE__HUMIDIFIER_DAY_END_HOUR


def _target_state() -> str | None:
    # humidifier only turns ON during daytime,
    # ON when humidity is below MIN, OFF above MAX, do nothing if its inbetween
    if not _is_daytime():
        return OFF_MESSAGE

    humidity: float = env.humidity()
    if humidity < SERVICE__HUMIDIFIER_HUMIDITY_MIN:
        return ON_MESSAGE
    if humidity > SERVICE__HUMIDIFIER_HUMIDITY_MAX:
        return OFF_MESSAGE
    return None


def initialize():
    global _last_sent_state
    _last_sent_state = None
    print("[HUMIDIFIER] initialized.")


def deinitialize():
    print("[HUMIDIFIER] deinitialized.")


def update():
    global _last_sent_state
    if not env.is_available():
        return

    target: str | None = _target_state()
    if target is None or target == _last_sent_state:
        return
    if mqtt.send_message(SERVICE__HUMIDIFIER_POWER_TOPIC, target):
        _last_sent_state = target
        print(f"[HUMIDIFIER] humidity at {env.humidity():.1f}% -> turning humidifier {target}.")
