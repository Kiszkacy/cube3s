# single source of the current time for the whole app.
# time.localtime() allocates a new tuple on every call, so it is expanded once per main loop iteration
# instead of once per module per frame

import time

from config import UTC_OFFSET


SECONDS_PER_DAY: int = 86400
UTC_OFFSET_SECONDS: int = UTC_OFFSET*3600


_utc_epoch: int = 0
_local_epoch: int = 0
_parts: tuple = time.localtime(0) # (year, month, day, hour, minute, second, weekday, yearday)

_second_changed: bool = True
_minute_changed: bool = True
_hour_changed: bool = True
_day_changed: bool = True


def update(): # IMPORTANT: has to be called once per main loop iteration, before the running module updates
    global _utc_epoch, _local_epoch, _parts
    global _second_changed, _minute_changed, _hour_changed, _day_changed

    utc_epoch: int = time.time()
    if utc_epoch == _utc_epoch:
        _second_changed = False
        _minute_changed = False
        _hour_changed = False
        _day_changed = False
        return

    previous: tuple = _parts

    _utc_epoch = utc_epoch
    _local_epoch = utc_epoch + UTC_OFFSET_SECONDS
    _parts = time.localtime(_local_epoch)

    _second_changed = True
    _minute_changed = _parts[4] != previous[4]
    _hour_changed = _parts[3] != previous[3]
    _day_changed = _parts[2] != previous[2]


def epoch() -> int:
    return _utc_epoch


def local_epoch() -> int:
    return _local_epoch


def parts() -> tuple:
    return _parts


def year() -> int:
    return _parts[0]


def month() -> int:
    return _parts[1]


def day() -> int:
    return _parts[2]


def hour() -> int:
    return _parts[3]


def minute() -> int:
    return _parts[4]


def second() -> int:
    return _parts[5]


def weekday() -> int: # 0 => monday, 1 => tuesday, ..., 6 => sunday
    return _parts[6]


def yearday() -> int:
    return _parts[7]


# IMPORTANT: these functions are only valid in the same main loop iteration as the module update() call
def second_changed() -> bool:
    return _second_changed


def minute_changed() -> bool:
    return _minute_changed


def hour_changed() -> bool:
    return _hour_changed


def day_changed() -> bool:
    return _day_changed


def date_string(day_offset: int = 0) -> str: # -1 => yesterday, 0 => today, 1 => tomorrow, etc.
    parts_: tuple = _parts if day_offset == 0 else time.localtime(_local_epoch + day_offset*SECONDS_PER_DAY)
    return "{:04d}-{:02d}-{:02d}".format(parts_[0], parts_[1], parts_[2])


def time_string(with_seconds: bool = False) -> str:
    if with_seconds:
        return "{:02d}:{:02d}:{:02d}".format(_parts[3], _parts[4], _parts[5])
    return "{:02d}:{:02d}".format(_parts[3], _parts[4])
