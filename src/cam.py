import camera
import jpg
# IMPORTANT: named "cam" instead of "camera" so it does not shadow the builtin driver module


DEFAULT_HORIZONTAL_FLIP: bool = True
DEFAULT_VERTICAL_FLIP: bool = False
DEFAULT_JPEG_QUALITY: int = 80 # 0 - 100


_is_enabled: bool = False # no isEnabled() method in the camera driver
_horizontal_flip: bool = DEFAULT_HORIZONTAL_FLIP
_vertical_flip: bool = DEFAULT_VERTICAL_FLIP


def enable(pixformat: int = camera.RGB565, framesize: int = camera.QVGA, flip_horizontally: bool = DEFAULT_HORIZONTAL_FLIP, flip_vertically: bool = DEFAULT_VERTICAL_FLIP) -> bool:
    global _is_enabled, _horizontal_flip, _vertical_flip
    try:
        camera.init(pixformat=pixformat, framesize=framesize)
        camera.set_hmirror(flip_horizontally)
        camera.set_vflip(flip_vertically)
        _horizontal_flip = flip_horizontally
        _vertical_flip = flip_vertically
        _is_enabled = True
        print("[CAMERA] enabled.")
    except Exception as e:
        print(f"[CAMERA] failed to enable: '{e}'.")
        _is_enabled = False
    return _is_enabled


def disable():
    global _is_enabled
    if _is_enabled:
        camera.deinit()
    _is_enabled = False
    print("[CAMERA] disabled.")


def is_enabled() -> bool:
    return _is_enabled


def is_flipped_horizontally() -> bool:
    return _horizontal_flip


def is_flipped_vertically() -> bool:
    return _vertical_flip


def flip_horizontally() -> bool:
    global _horizontal_flip
    _horizontal_flip = not _horizontal_flip
    camera.set_hmirror(_horizontal_flip)
    return _horizontal_flip


def flip_vertically() -> bool:
    global _vertical_flip
    _vertical_flip = not _vertical_flip
    camera.set_vflip(_vertical_flip)
    return _vertical_flip


def reset_horizontal_flip():
    global _horizontal_flip
    _horizontal_flip = DEFAULT_HORIZONTAL_FLIP
    camera.set_hmirror(_horizontal_flip)


def reset_vertical_flip():
    global _vertical_flip
    _vertical_flip = DEFAULT_VERTICAL_FLIP
    camera.set_vflip(_vertical_flip)


def snapshot() -> object:
    return camera.snapshot()


def encode_jpeg(img: object, quality: int = DEFAULT_JPEG_QUALITY) -> object: # returns a jpg object exposing .bytearray() and .size()
    return jpg.encode(img, quality)
