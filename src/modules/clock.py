import math
import time

import display
import localtime
import mqtt
import common
import power
import router
import speaker
import touch
import ui
from config import CLOCK__MQTT_BRIGHTNESS_SWITCH_TOPIC, CLOCK__MQTT_MODE_SWITCH_TOPIC
from ui import COLOR_WHITE


SERVICES: tuple[str, ...] = ("auto_brightness", "humidifier")


DIGITAL_CLOCK_TEXT_SIZE: float = 10.0
DIGITAL_CLOCK_SECONDS_TEXT_SIZE: float = 4.0
DIGITAL_CLOCK_COLOR: int = COLOR_WHITE
DIGITAL_CLOCK_SECONDS_COLOR: int = 0xAAAAAA # light gray
DIGITAL_CLOCK_TEXT_X: int = display.WIDTH // 2 - 16
DIGITAL_CLOCK_SECONDS_TEXT_X: int = display.WIDTH // 2 + 136
DIGITAL_CLOCK_SECONDS_TEXT_Y: int = display.HEIGHT // 2 + 16 + 2
DIGITAL_CLOCK_COLON_GAP: int = 10

ANALOG_CLOCK_CENTER_X: int = display.WIDTH // 2
ANALOG_CLOCK_CENTER_Y: int = display.HEIGHT // 2
ANALOG_CLOCK_RADIUS: int = 100
ANALOG_CLOCK_HOUR_HAND_LENGTH: int = 50
ANALOG_CLOCK_MINUTE_HAND_LENGTH: int = 70
ANALOG_CLOCK_SECOND_HAND_LENGTH: int = 90
ANALOG_CLOCK_BORDER_COLOR: int = COLOR_WHITE
ANALOG_CLOCK_HOUR_HAND_COLOR: int = COLOR_WHITE
ANALOG_CLOCK_MINUTE_HAND_COLOR: int = COLOR_WHITE
ANALOG_CLOCK_SECOND_HAND_COLOR: int = 0xFF0000 # red
ANALOG_CLOCK_HOUR_TICK_LENGTH: int = 4

BATTERY_ICON_WIDTH: int = 48
BATTERY_ICON_HEIGHT: int = 28
BATTERY_NUB_WIDTH: int = 4
BATTERY_NUB_HEIGHT: int = 12
BATTERY_ICON_X: int = display.WIDTH - BATTERY_ICON_WIDTH - BATTERY_NUB_WIDTH - ui.SCREEN_PADDING
BATTERY_ICON_Y: int = ui.SCREEN_PADDING
BATTERY_BACKGROUND_COLOR: int = 0x555555 # dark gray
BATTERY_CHARGING_COLOR: int = 0x00FFFF # cyan
BATTERY_HIGH_COLOR: int = 0x00FF00 # green
BATTERY_MEDIUM_COLOR: int = 0xFFFF00 # yellow
BATTERY_LOW_COLOR: int = 0xFF0000 # red
BATTERY_LEVEL_PADDING: int = 4
BATTERY_BOLT_HALF_WIDTH: int = 5
BATTERY_BOLT_HALF_HEIGHT: int = 9
BATTERY_BOLT_NOTCH: int = 3

SWITCH_BUTTON: tuple = ui.rect(
    display.WIDTH - 44 - ui.SCREEN_PADDING,
    display.HEIGHT - 36 - ui.SCREEN_PADDING,
    44,
    36
)
SWITCH_BUTTON_FILL_COLOR: int = 0x004040 # dark cyan
BACK_TO_DASHBOARD_BUTTON: tuple = ui.rect(
    ui.SCREEN_PADDING,
    ui.SCREEN_PADDING,
    44,
    36
)
BACK_TO_DASHBOARD_BUTTON_FILL_COLOR: int = 0x400000 # dark red
BUTTON_BORDER_COLOR: int = COLOR_WHITE
BUTTON_TEXT_COLOR: int = COLOR_WHITE
BUTTON_TEXT_SIZE: float = 2.0

TOUCH_INACTIVITY_TIMEOUT_MS: int = 10000

_mode: int = 0  # 0 => digital, 1 => analog
_previous_mode: int = -1
_previous_awake: bool = True

_awake: bool = True # whether the ui reacts to touch and shows the switch button
_last_interaction_timestamp: int = time.ticks_ms()
_ignore_touch_until_release: bool = False # true while consuming the wake touch


def on_mqtt_mode_switch(topic: str, message: bytes):
    global _mode
    message_: str = message.decode('utf-8').lower().strip()
    if message_ in ("0", "digital"):
        _mode = 0
    elif message_ in ("1", "analog"):
        _mode = 1
    elif message_ == "toggle":
        _mode = 1 - _mode
    print(f"[CLOCK.MQTT] mode switched to: {'digital' if _mode == 0 else 'analog'}.")


def on_mqtt_brightness(topic: str, message: bytes):
    try:
        brightness: int = int(message.decode('utf-8'))
        clamped_brightness: int = max(10, min(255, brightness))
        display.set_brightness(clamped_brightness)
    except ValueError:
        return
    print(f"[CLOCK.MQTT] brightness set to: {display.get_brightness()}.")


def initialize():
    global _previous_mode, _previous_awake, _awake, _last_interaction_timestamp, _ignore_touch_until_release
    display.use_canvas()

    _previous_mode = -1
    _previous_awake = True
    _awake = True
    _last_interaction_timestamp = time.ticks_ms()
    _ignore_touch_until_release = False

    # TODO: register_handler will be called multiple times if the module is switched back and forth
    # TODO: add unregister_handler ? or another idea
    mqtt.register_handler(CLOCK__MQTT_MODE_SWITCH_TOPIC, on_mqtt_mode_switch)
    mqtt.subscribe(CLOCK__MQTT_MODE_SWITCH_TOPIC)
    mqtt.register_handler(CLOCK__MQTT_BRIGHTNESS_SWITCH_TOPIC, on_mqtt_brightness)
    mqtt.subscribe(CLOCK__MQTT_BRIGHTNESS_SWITCH_TOPIC)

    speaker.enable()

    print("[CLOCK] initialized.")


def deinitialize():
    display.clear_canvas()
    display.flush_canvas()
    display.use_display()

    speaker.disable()

    mqtt.unsubscribe(CLOCK__MQTT_MODE_SWITCH_TOPIC)
    mqtt.unsubscribe(CLOCK__MQTT_BRIGHTNESS_SWITCH_TOPIC)

    print("[CLOCK] deinitialized.")


def handle_touch():
    global _mode, _awake, _last_interaction_timestamp, _ignore_touch_until_release

    if not touch.is_pressed():
        _ignore_touch_until_release = False
        return

    if not _awake: # first touch after inactivity => wake up the ui, do not do anything else yet
        _awake = True
        _ignore_touch_until_release = True
        _last_interaction_timestamp = time.ticks_ms()
        return

    # update last known touch interaction time
    _last_interaction_timestamp = time.ticks_ms()

    if _ignore_touch_until_release:
        return

    x, y = touch.position()
    if ui.is_inside(x, y, SWITCH_BUTTON) and touch.was_pressed():
        # inside switch button => switch mode
        _mode = 1 - _mode
        speaker.beep()
    elif ui.is_inside(x, y, BACK_TO_DASHBOARD_BUTTON) and touch.was_pressed():
        router.request_module_switch("dashboard")
    else:
        # outside switch button => adjust brightness
        common.set_brightness_from_vertical_position(y)


def draw_digital_clock():
    hours, minutes, seconds = localtime.hour(), localtime.minute(), localtime.second()

    y: int = display.HEIGHT // 2
    display.set_text_color(DIGITAL_CLOCK_COLOR)
    display.set_text_size(DIGITAL_CLOCK_TEXT_SIZE)
    display.draw_text(":", x=DIGITAL_CLOCK_TEXT_X, y=y, anchor=display.MIDDLE_CENTER)
    display.draw_text(f"{hours:02}", x=DIGITAL_CLOCK_TEXT_X - DIGITAL_CLOCK_COLON_GAP, y=y, anchor=display.MIDDLE_RIGHT)
    display.draw_text(f"{minutes:02}", x=DIGITAL_CLOCK_TEXT_X + DIGITAL_CLOCK_COLON_GAP, y=y, anchor=display.MIDDLE_LEFT)

    display.draw_text( # smaller seconds on the right
        f"{seconds:02}",
        x=DIGITAL_CLOCK_SECONDS_TEXT_X,
        y=DIGITAL_CLOCK_SECONDS_TEXT_Y,
        size=DIGITAL_CLOCK_SECONDS_TEXT_SIZE,
        anchor=display.MIDDLE_CENTER,
        color=DIGITAL_CLOCK_SECONDS_COLOR
    )


def draw_analog_clock():
    hours, minutes, seconds = localtime.hour(), localtime.minute(), localtime.second()

    display.draw_circle(ANALOG_CLOCK_CENTER_X, ANALOG_CLOCK_CENTER_Y, ANALOG_CLOCK_RADIUS, color=ANALOG_CLOCK_BORDER_COLOR) # clock border
    display.draw_circle(ANALOG_CLOCK_CENTER_X, ANALOG_CLOCK_CENTER_Y, 4, color=ANALOG_CLOCK_BORDER_COLOR, fill=True) # clock center

    for i in range(12):
        angle: float = math.radians(i * 30)
        x_outer: int = int(ANALOG_CLOCK_CENTER_X + ANALOG_CLOCK_RADIUS * math.sin(angle))
        y_outer: int = int(ANALOG_CLOCK_CENTER_Y - ANALOG_CLOCK_RADIUS * math.cos(angle))
        x_inner: int = int(ANALOG_CLOCK_CENTER_X + (ANALOG_CLOCK_RADIUS - ANALOG_CLOCK_HOUR_TICK_LENGTH) * math.sin(angle))
        y_inner: int = int(ANALOG_CLOCK_CENTER_Y - (ANALOG_CLOCK_RADIUS - ANALOG_CLOCK_HOUR_TICK_LENGTH) * math.cos(angle))
        display.draw_line(x_inner, y_inner, x_outer, y_outer, color=ANALOG_CLOCK_BORDER_COLOR)

    hour_angle: float = math.radians(((hours % 12) + minutes / 60.0) * 30)
    minute_angle: float = math.radians((minutes + seconds / 60.0) * 6)
    second_angle: float = math.radians(seconds * 6)

    hour_x: int = int(ANALOG_CLOCK_CENTER_X + ANALOG_CLOCK_HOUR_HAND_LENGTH * math.sin(hour_angle))
    hour_y: int = int(ANALOG_CLOCK_CENTER_Y - ANALOG_CLOCK_HOUR_HAND_LENGTH * math.cos(hour_angle))
    display.draw_line(ANALOG_CLOCK_CENTER_X, ANALOG_CLOCK_CENTER_Y, hour_x, hour_y, color=ANALOG_CLOCK_HOUR_HAND_COLOR)

    minute_x: int = int(ANALOG_CLOCK_CENTER_X + ANALOG_CLOCK_MINUTE_HAND_LENGTH * math.sin(minute_angle))
    minute_y: int = int(ANALOG_CLOCK_CENTER_Y - ANALOG_CLOCK_MINUTE_HAND_LENGTH * math.cos(minute_angle))
    display.draw_line(ANALOG_CLOCK_CENTER_X, ANALOG_CLOCK_CENTER_Y, minute_x, minute_y, color=ANALOG_CLOCK_MINUTE_HAND_COLOR)

    second_x: int = int(ANALOG_CLOCK_CENTER_X + ANALOG_CLOCK_SECOND_HAND_LENGTH * math.sin(second_angle))
    second_y: int = int(ANALOG_CLOCK_CENTER_Y - ANALOG_CLOCK_SECOND_HAND_LENGTH * math.cos(second_angle))
    display.draw_line(ANALOG_CLOCK_CENTER_X, ANALOG_CLOCK_CENTER_Y, second_x, second_y, color=ANALOG_CLOCK_SECOND_HAND_COLOR)


def draw_battery_bolt(center_x: int, center_y: int, color: int):
    display.draw_triangle( # upper half of the bolt
        center_x + BATTERY_BOLT_HALF_WIDTH, center_y - BATTERY_BOLT_HALF_HEIGHT,
        center_x - BATTERY_BOLT_HALF_WIDTH, center_y + BATTERY_BOLT_NOTCH,
        center_x, center_y + BATTERY_BOLT_NOTCH,
        color=color,
        fill=True
    )
    display.draw_triangle( # lower half, mirrored
        center_x - BATTERY_BOLT_HALF_WIDTH, center_y + BATTERY_BOLT_HALF_HEIGHT,
        center_x + BATTERY_BOLT_HALF_WIDTH, center_y - BATTERY_BOLT_NOTCH,
        center_x, center_y - BATTERY_BOLT_NOTCH,
        color=color,
        fill=True
    )


def draw_battery():
    battery_level: int = power.battery_level()
    is_battery_charging: bool = power.is_charging()
    is_usb_connected: bool = power.is_usb_connected()
    is_battery_present: bool = power.is_battery_present()

    battery_color: int = BATTERY_BACKGROUND_COLOR
    if is_battery_charging or is_usb_connected:
        battery_color = BATTERY_CHARGING_COLOR
    elif battery_level > 60:
        battery_color = BATTERY_HIGH_COLOR
    elif battery_level > 20:
        battery_color = BATTERY_MEDIUM_COLOR
    else:
        battery_color = BATTERY_LOW_COLOR

    display.draw_round_rect( # battery body
        x=BATTERY_ICON_X,
        y=BATTERY_ICON_Y,
        width=BATTERY_ICON_WIDTH,
        height=BATTERY_ICON_HEIGHT,
        radius=2,
        color=BATTERY_BACKGROUND_COLOR,
        fill=True
    )
    display.draw_rect( # battery nub on the right side
        x=BATTERY_ICON_X + BATTERY_ICON_WIDTH,
        y=BATTERY_ICON_Y + (BATTERY_ICON_HEIGHT - BATTERY_NUB_HEIGHT) // 2,
        width=BATTERY_NUB_WIDTH,
        height=BATTERY_NUB_HEIGHT,
        color=BATTERY_BACKGROUND_COLOR,
        fill=True
    )

    # usb powered while the battery is switched off => draw a bolt instead of a level bar
    if not is_battery_present:
        draw_battery_bolt(
            center_x=BATTERY_ICON_X + BATTERY_ICON_WIDTH//2, center_y=BATTERY_ICON_Y + BATTERY_ICON_HEIGHT//2, color=BATTERY_CHARGING_COLOR
        )
    else:
        battery_level_max_width: int = BATTERY_ICON_WIDTH - 2*BATTERY_LEVEL_PADDING
        display.draw_round_rect( # actual battery level, fills left -> right
            x=BATTERY_ICON_X + BATTERY_LEVEL_PADDING,
            y=BATTERY_ICON_Y + BATTERY_LEVEL_PADDING,
            width=max(1, int(battery_level_max_width * (battery_level/100))),
            height=BATTERY_ICON_HEIGHT - 2*BATTERY_LEVEL_PADDING,
            radius=2,
            color=battery_color,
            fill=True
        )


def draw_buttons():
    ui.draw_button(
        SWITCH_BUTTON,
        label="ANA" if _mode == 0 else "DIG",
        fill_color=SWITCH_BUTTON_FILL_COLOR,
        border_color=BUTTON_BORDER_COLOR,
        text_color=BUTTON_TEXT_COLOR,
        text_size=BUTTON_TEXT_SIZE
    )

    ui.draw_button(
        BACK_TO_DASHBOARD_BUTTON,
        label="BCK",
        fill_color=BACK_TO_DASHBOARD_BUTTON_FILL_COLOR,
        border_color=BUTTON_BORDER_COLOR,
        text_color=BUTTON_TEXT_COLOR,
        text_size=BUTTON_TEXT_SIZE
    )


def update():
    global _previous_mode, _previous_awake, _awake

    handle_touch() # handle touch at every update loop

    # hide the switch button and sleep touch after was not touched for a while
    if _awake and time.ticks_diff(time.ticks_ms(), _last_interaction_timestamp) > TOUCH_INACTIVITY_TIMEOUT_MS:
        _awake = False

    if _previous_mode != _mode or localtime.second_changed() or _previous_awake != _awake:
        _previous_mode = _mode
        _previous_awake = _awake

        # redraw only if mode changed, second changed or button visibility changed
        display.clear_canvas()

        if _mode == 0:
            draw_digital_clock()
        elif _mode == 1:
            draw_analog_clock()

        if _awake:
            draw_battery()
            draw_buttons()

        display.flush_canvas()
