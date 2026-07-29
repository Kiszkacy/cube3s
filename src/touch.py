import M5 # type: ignore


_touch: M5.Touch = M5.Touch

# TODO: cleanup and rename some to easier understand which call does what
# TODO: https://docs.m5stack.com/en/arduino/m5unified/touch_class#touch-detail


def offset_x(touch_index: int = 0) -> int: # distance since last sampling
    return _touch.getDetail(touch_index)[0]


def offset_y(touch_index: int = 0) -> int: # distance since last sampling
    return _touch.getDetail(touch_index)[1]


def distance_x(touch_index: int = 0) -> int: # distance since first sample
    return _touch.getDetail(touch_index)[2]


def distance_y(touch_index: int = 0) -> int: # distance since first sample
    return _touch.getDetail(touch_index)[3]


def is_pressed(touch_index: int = 0) -> bool:
    return _touch.getDetail(touch_index)[4]


def was_pressed(touch_index: int = 0) -> bool:
    return _touch.getDetail(touch_index)[5]


def was_clicked(touch_index: int = 0) -> bool:
    return _touch.getDetail(touch_index)[6]


def is_released(touch_index: int = 0) -> bool:
    return _touch.getDetail(touch_index)[7]


def was_released(touch_index: int = 0) -> bool:
    return _touch.getDetail(touch_index)[8]


def is_holding(touch_index: int = 0) -> bool:
    return _touch.getDetail(touch_index)[9]


def was_held(touch_index: int = 0) -> bool: # user started holding
    return _touch.getDetail(touch_index)[10]


def touch_count() -> int:
    return _touch.getCount()


def position() -> tuple[int, int]:
    return _touch.getX(), _touch.getY()


def x_position() -> int:
    return _touch.getX()


def y_position() -> int:
    return _touch.getY()
