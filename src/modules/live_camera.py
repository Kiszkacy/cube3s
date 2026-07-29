import camera
import display
import touch


_is_working: bool = False
_printed_error_message: bool = False


def initialize():
    global _is_working
    try:
        camera.init(pixformat=camera.RGB565, framesize=camera.QVGA)

        camera.set_hmirror(True)
        camera.set_vflip(False)

        _is_working = True
        print("[CAMERA] successfully initialized in QVGA RGB565 mode.")
    except Exception as e:
        print(f"[CAMERA] failed to initialize camera: '{e}'.")
        _is_working = False


def deinitialize():
    global _is_working
    if _is_working:
        camera.deinit()
    _is_working = False
    display.clear_screen()
    print("[CAMERA] deinitialized.")


def update():
    global _printed_error_message
    if not _is_working and _printed_error_message: # print the error message only once
        return
    
    if not _is_working:
        display.draw_text("Camera Init Error", x=display.WIDTH//2, y=display.HEIGHT//2, anchor="middle_center", color=0xFF0000)
        _printed_error_message = True
        return

    if touch.is_pressed():
        y: int = touch.y_position()
        brightness: int = int(255 * (1.0 - (y / display.HEIGHT)))
        clamped_brightness: int = max(10, min(255, brightness))
        display.set_brightness(clamped_brightness)

    # TODO: camera helper module ?
    img = camera.snapshot()
    if img is not None:
        display.draw_image(img, width=320, height=240)