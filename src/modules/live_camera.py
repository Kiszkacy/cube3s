import cam
import display
import touch
import common


_printed_error_message: bool = False


def initialize():
    global _printed_error_message
    _printed_error_message = False
    cam.enable()


def deinitialize():
    cam.disable()
    display.clear_screen()


def update():
    global _printed_error_message
    if not cam.is_enabled() and _printed_error_message: # print the error message only once
        return

    if not cam.is_enabled():
        display.draw_text("Camera Init Error", x=display.WIDTH//2, y=display.HEIGHT//2, anchor=display.MIDDLE_CENTER, color=0xFF0000)
        _printed_error_message = True
        return

    if touch.is_pressed():
        common.set_brightness_from_vertical_position(touch.y_position())

    img: object = cam.snapshot()
    if img is not None:
        display.draw_image(img, width=display.WIDTH, height=display.HEIGHT)