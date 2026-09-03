import time

from hardware import I2C, Pin # type: ignore
from unit import ENVUnit # type: ignore

# IMPORTANT: every getter here returns the value sampled by update(), a __RS variant reads the value immediately

# CoreS3 PORT.A (red, next to USB-C): SCL = GPIO1, SDA = GPIO2
PORT_A_SCL: int = 1
PORT_A_SDA: int = 2
I2C_FREQ: int = 100000

# ENV III = SHT30 (temp/humidity) + QMP6988 (pressure)
SHT30_ADDRESS: int = 0x44
QMP6988_ADDRESS: int = 0x70

SAMPLE_INTERVAL_MS: int = 30000 # 30 seconds

_i2c: I2C = I2C(0, scl=Pin(PORT_A_SCL), sda=Pin(PORT_A_SDA), freq=I2C_FREQ)
_env: ENVUnit = ENVUnit(i2c=_i2c, type=3)

_next_sample_timestamp: int = 0
_temperature: float = 0.0
_humidity: float = 0.0
_pressure: float = 0.0
_available: bool = False


def resample():
    global _next_sample_timestamp, _temperature, _humidity, _pressure, _available
    _next_sample_timestamp = time.ticks_add(time.ticks_ms(), SAMPLE_INTERVAL_MS)

    try:
        _temperature = _env.read_temperature()
        _humidity = _env.read_humidity()
        _pressure = _env.read_pressure()
        if not _available:
            print("[ENV] sensor available.")
        _available = True
    except Exception as e:
        if _available:
            print(f"[ENV] sensor unavailable: '{e}'.")
        _available = False


def update(): # IMPORTANT: has to be called once per main loop iteration, before the running module updates
    if time.ticks_diff(time.ticks_ms(), _next_sample_timestamp) < 0:
        return
    resample()


def _probe() -> bool:
    try:
        addresses = _i2c.scan() # TODO: typehint
    except Exception:
        return False
    return SHT30_ADDRESS in addresses and QMP6988_ADDRESS in addresses


def is_available() -> bool:
    return _available


def is_available__RS() -> bool:
    global _available
    _available = _probe()
    return _available


def temperature() -> float: # celsius
    return _temperature


def temperature__RS() -> float:
    global _temperature
    _temperature = _env.read_temperature()
    return _temperature


def humidity() -> float: # percent relative humidity
    return _humidity


def humidity__RS() -> float:
    global _humidity
    _humidity = _env.read_humidity()
    return _humidity


def pressure() -> float: # hPa
    return _pressure


def pressure__RS() -> float:
    global _pressure
    _pressure = _env.read_pressure()
    return _pressure
