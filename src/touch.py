import M5 # type: ignore


_touch: M5.Touch = M5.Touch

# TODO: cleanup and rename some touch functions to make it easier to understand which call does what
# TODO: https://docs.m5stack.com/en/arduino/m5unified/touch_class#touch-detail

# IMPORTANT: every getter here returns the value sampled by update(), a __RS variant reads the value immediately

# (offset_x, offset_y, distance_x, distance_y, is_pressed, was_pressed, was_clicked, is_released, was_released, is_holding, was_held)
_NOT_TOUCHED_DETAIL: tuple = (0, 0, 0, 0, False, False, False, True, False, False, False)

_detail: tuple = _NOT_TOUCHED_DETAIL
_x: int = 0
_y: int = 0


def update(touch_index: int = 0): # IMPORTANT: has to be called once per main loop iteration, before the running module updates
    global _detail, _x, _y
    _detail = _touch.getDetail(touch_index)
    _x = _touch.getX()
    _y = _touch.getY()


def detail() -> tuple:
    return _detail


def detail__RS(touch_index: int = 0) -> tuple: # TODO: the only way of getting second touch point detail, improve ?
    return _touch.getDetail(touch_index)


def offset_x() -> int: # distance since last sampling
    return _detail[0]


def offset_y() -> int: # distance since last sampling
    return _detail[1]


def distance_x() -> int: # distance since first sample
    return _detail[2]


def distance_y() -> int: # distance since first sample
    return _detail[3]


def is_pressed() -> bool:
    return _detail[4]


def was_pressed() -> bool:
    return _detail[5]


def was_clicked() -> bool:
    return _detail[6]


def is_released() -> bool:
    return _detail[7]


def was_released() -> bool:
    return _detail[8]


def is_holding() -> bool:
    return _detail[9]


def was_held() -> bool: # user started holding at this frame
    return _detail[10]


def touch_count() -> int:
    return _touch.getCount()


def position() -> tuple[int, int]:
    return _x, _y


def position__RS() -> tuple[int, int]:
    return _touch.getX(), _touch.getY()


def x_position() -> int:
    return _x


def x_position__RS() -> int:
    return _touch.getX()


def y_position() -> int:
    return _y


def y_position__RS() -> int:
    return _touch.getY()
