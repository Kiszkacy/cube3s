import M5 # type: ignore


_touch: M5.Touch = M5.Touch


def is_touched() -> bool:
    return _touch.getCount() > 0


def touch_count() -> int:
    return _touch.getCount()


def position(touch_index: int = 0) -> tuple[int, int]:
    return _touch.getX(touch_index), _touch.getY(touch_index)


def x_position(touch_index: int = 0) -> int:
    return _touch.getX(touch_index)


def y_position(touch_index: int = 0) -> int:
    return _touch.getY(touch_index)
