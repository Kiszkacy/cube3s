import time
import display
import mqtt
import touch
import math
from config import *

import M5 # type: ignore


# TODO: implement sound helper module and play sounds on mode switch

DIGITAL_CLOCK_TEXT_SIZE: float = 5.0
DIGITAL_CLOCK_COLOR: int = 0xFFFFFF # white

ANALOG_CLOCK_CENTER_X: int = display.WIDTH // 2
ANALOG_CLOCK_CENTER_Y: int = display.HEIGHT // 2
ANALOG_CLOCK_RADIUS: int = 100
ANALOG_CLOCK_HOUR_HAND_LENGTH: int = 50
ANALOG_CLOCK_MINUTE_HAND_LENGTH: int = 70
ANALOG_CLOCK_SECOND_HAND_LENGTH: int = 90
ANALOG_CLOCK_BORDER_COLOR: int = 0xFFFFFF # white
ANALOG_CLOCK_HOUR_HAND_COLOR: int = 0xFFFFFF # white
ANALOG_CLOCK_MINUTE_HAND_COLOR: int = 0xFFFFFF # white
ANALOG_CLOCK_SECOND_HAND_COLOR: int = 0xFF0000 # red
ANALOG_CLOCK_HOUR_HAND_WIDTH: int = 4
ANALOG_CLOCK_MINUTE_HAND_WIDTH: int = 2
ANALOG_CLOCK_SECOND_HAND_WIDTH: int = 1
ANALOG_CLOCK_HOUR_TICK_LENGTH: int = 4
ANALOG_CLOCK_HOUR_TICK_WIDTH: int = 2

BATTERY_ICON_WIDTH: int = 20
BATTERY_ICON_HEIGHT: int = 40
BATTERY_ICON_X: int = 10
BATTERY_ICON_Y: int = 10
BATTERY_BACKGROUND_COLOR: int = 0x555555 # dark gray
BATTERY_CHARGING_COLOR: int = 0x00FFFF # cyan
BATTERY_HIGH_COLOR: int = 0x00FF00 # green
BATTERY_MEDIUM_COLOR: int = 0xFFFF00 # yellow
BATTERY_LOW_COLOR: int = 0xFF0000 # red
BATTERY_LEVEL_PADDING: int = 2
BATTERY_TOP_PADDING: int = 4
BATTERY_TOP_HEIGHT: int = 4

SWITCH_BUTTON_WIDTH: int = 60
SWITCH_BUTTON_HEIGHT: int = 40
SWITCH_BUTTON_X: int = display.WIDTH - SWITCH_BUTTON_WIDTH - 10
SWITCH_BUTTON_Y: int = display.HEIGHT - SWITCH_BUTTON_HEIGHT - 10
SWITCH_BUTTON_FILL_COLOR: int = 0x004040 # dark cyan
SWITCH_BUTTON_BORDER_COLOR: int = 0xFFFFFF # white

_mode: int = 0  # 0 => digital, 1 => analog
_previous_mode: int = -1
_previous_second: int = -1


def on_mqtt_mode_switch(topic: str, message: str):
    global _mode
    message_: str = message.lower().strip()
    if message_ in ("0", "digital"):
        _mode = 0
    elif message_ in ("1", "analog"):
        _mode = 1
    elif message_ == "toggle":
        _mode = 1 - _mode
    print(f"[CLOCK.MQTT] mode switched to: {'digital' if _mode == 0 else 'analog'}.")
    

def on_mqtt_brightness(topic: str, message: str):
    try:
        brightness: int = int(message)
        clamped_brightness: int = max(10, min(255, brightness))
        display.set_brightness(clamped_brightness)
    except ValueError:
        return
    print(f"[CLOCK.MQTT] brightness set to: {display.get_brightness()}.")


def initialize():
    display.use_canvas()

    mqtt.register_handler(CLOCK__MQTT_MODE_SWITCH_TOPIC, on_mqtt_mode_switch)
    mqtt.subscribe(CLOCK__MQTT_MODE_SWITCH_TOPIC)
    mqtt.register_handler(CLOCK__MQTT_BRIGHTNESS_SWITCH_TOPIC, on_mqtt_brightness)
    mqtt.subscribe(CLOCK__MQTT_BRIGHTNESS_SWITCH_TOPIC)
    
    print("[CLOCK] initialized.")


def deinitialize():
    display.clear_canvas()
    display.flush_canvas()
    display.use_display()

    mqtt.unsubscribe(CLOCK__MQTT_MODE_SWITCH_TOPIC)
    mqtt.unsubscribe(CLOCK__MQTT_BRIGHTNESS_SWITCH_TOPIC)
    
    print("[CLOCK] deinitialized.")


def handle_touch():
    global _mode
    if not touch.is_pressed():
        return

    x, y = touch.position()
    is_inside_button: bool = (SWITCH_BUTTON_X <= x <= SWITCH_BUTTON_X + SWITCH_BUTTON_WIDTH) and (
            SWITCH_BUTTON_Y <= y <= SWITCH_BUTTON_Y + SWITCH_BUTTON_HEIGHT
    )

    if is_inside_button:
        # inside switch button => switch mode
        if touch.was_pressed():
            _mode = 1 - _mode
    else :
        # outside switch button => adjust brightness
        brightness: int = int(255 * (1.0 - (y / display.HEIGHT)))
        clamped_brightness: int = max(10, min(255, brightness))
        display.set_brightness(clamped_brightness)


def draw_digital_clock():
    now: time.struct_time = time.localtime(time.time() + UTC_OFFSET*3600)
    hours, minutes, seconds = now[3], now[4], now[5]

    display.draw_text(
        f"{hours:02}:{minutes:02}:{seconds:02}",
        x=display.WIDTH//2,
        y=display.HEIGHT//2,
        size=DIGITAL_CLOCK_TEXT_SIZE,
        anchor="middle_center",
        color=DIGITAL_CLOCK_COLOR
    )


def draw_analog_clock():
    now: time.struct_time = time.localtime(time.time() + UTC_OFFSET*3600)
    hours, minutes, seconds = now[3], now[4], now[5]

    display.draw_circle(ANALOG_CLOCK_CENTER_X, ANALOG_CLOCK_CENTER_Y, ANALOG_CLOCK_RADIUS, color=ANALOG_CLOCK_BORDER_COLOR) # clock border
    display.draw_circle(ANALOG_CLOCK_CENTER_X, ANALOG_CLOCK_CENTER_Y, 4, color=ANALOG_CLOCK_BORDER_COLOR, fill=True) # clock center

    for i in range(12):
        angle: float = math.radians(i * 30)
        x_outer: int = int(ANALOG_CLOCK_CENTER_X + ANALOG_CLOCK_RADIUS * math.sin(angle))
        y_outer: int = int(ANALOG_CLOCK_CENTER_Y - ANALOG_CLOCK_RADIUS * math.cos(angle))
        x_inner: int = int(ANALOG_CLOCK_CENTER_X + (ANALOG_CLOCK_RADIUS - ANALOG_CLOCK_HOUR_TICK_LENGTH) * math.sin(angle))
        y_inner: int = int(ANALOG_CLOCK_CENTER_Y - (ANALOG_CLOCK_RADIUS - ANALOG_CLOCK_HOUR_TICK_LENGTH) * math.cos(angle))
        display.draw_line(x_inner, y_inner, x_outer, y_outer, color=ANALOG_CLOCK_BORDER_COLOR, width=ANALOG_CLOCK_HOUR_TICK_WIDTH)

    hour_angle: float = math.radians(((hours % 12) + minutes / 60.0) * 30)
    minute_angle: float = math.radians((minutes + seconds / 60.0) * 6)
    second_angle: float = math.radians(seconds * 6)

    hour_x: int = int(ANALOG_CLOCK_CENTER_X + (ANALOG_CLOCK_HOUR_HAND_LENGTH) * math.sin(hour_angle))
    hour_y: int = int(ANALOG_CLOCK_CENTER_Y - (ANALOG_CLOCK_HOUR_HAND_LENGTH) * math.cos(hour_angle))
    display.draw_line(ANALOG_CLOCK_CENTER_X, ANALOG_CLOCK_CENTER_Y, hour_x, hour_y, color=ANALOG_CLOCK_HOUR_HAND_COLOR, width=ANALOG_CLOCK_HOUR_HAND_WIDTH)

    minute_x: int = int(ANALOG_CLOCK_CENTER_X + (ANALOG_CLOCK_MINUTE_HAND_LENGTH) * math.sin(minute_angle))
    minute_y: int = int(ANALOG_CLOCK_CENTER_Y - (ANALOG_CLOCK_MINUTE_HAND_LENGTH) * math.cos(minute_angle))
    display.draw_line(ANALOG_CLOCK_CENTER_X, ANALOG_CLOCK_CENTER_Y, minute_x, minute_y, color=ANALOG_CLOCK_MINUTE_HAND_COLOR, width=ANALOG_CLOCK_MINUTE_HAND_WIDTH)

    second_x: int = int(ANALOG_CLOCK_CENTER_X + (ANALOG_CLOCK_SECOND_HAND_LENGTH) * math.sin(second_angle))
    second_y: int = int(ANALOG_CLOCK_CENTER_Y - (ANALOG_CLOCK_SECOND_HAND_LENGTH) * math.cos(second_angle))
    display.draw_line(ANALOG_CLOCK_CENTER_X, ANALOG_CLOCK_CENTER_Y, second_x, second_y, color=ANALOG_CLOCK_SECOND_HAND_COLOR, width=ANALOG_CLOCK_SECOND_HAND_WIDTH)


def draw_battery():
    # TODO: implement proper power helper module
    battery_level: int = M5.Power.getBatteryLevel()
    is_battery_charging: bool = M5.Power.isCharging()
    is_usb_connected: bool = M5.Power.getVBUSVoltage() > 4000

    battery_color: int = BATTERY_BACKGROUND_COLOR
    if is_battery_charging or is_usb_connected:
        battery_color = BATTERY_CHARGING_COLOR
    elif battery_level > 60:
        battery_color = BATTERY_HIGH_COLOR
    elif battery_level > 20:
        battery_color = BATTERY_MEDIUM_COLOR
    else:
        battery_color = BATTERY_LOW_COLOR

    display.draw_rect( # battery background
        x=BATTERY_ICON_X,
        y=BATTERY_ICON_Y,
        width=BATTERY_ICON_WIDTH,
        height=BATTERY_ICON_HEIGHT,
        color=BATTERY_BACKGROUND_COLOR,
        fill=True
    )
    display.draw_rect( # battery top
        x=BATTERY_ICON_X+BATTERY_TOP_PADDING,
        y=BATTERY_ICON_Y-BATTERY_TOP_HEIGHT,
        width=BATTERY_ICON_WIDTH-2*BATTERY_TOP_PADDING,
        height=BATTERY_TOP_HEIGHT,
        color=BATTERY_BACKGROUND_COLOR,
        fill=True
    )
    battery_level_max_height: int = int((BATTERY_ICON_HEIGHT-2*BATTERY_LEVEL_PADDING))
    display.draw_round_rect( # actual battery level
        x=BATTERY_ICON_X+BATTERY_LEVEL_PADDING, 
        y=int(BATTERY_ICON_Y+BATTERY_LEVEL_PADDING+(battery_level_max_height*(100-battery_level)/100)),
        width=(BATTERY_ICON_WIDTH-2*BATTERY_LEVEL_PADDING),
        height=int(battery_level_max_height*(battery_level/100)),
        radius=4,
        color=battery_color,
        fill=True
    )


def draw_switch_mode_button():
    display.draw_round_rect(
        SWITCH_BUTTON_X, SWITCH_BUTTON_Y, SWITCH_BUTTON_WIDTH, SWITCH_BUTTON_HEIGHT,
        radius=8,
        color=SWITCH_BUTTON_FILL_COLOR,
        fill=True
    )
    display.draw_round_rect(
        SWITCH_BUTTON_X, SWITCH_BUTTON_Y, SWITCH_BUTTON_WIDTH, SWITCH_BUTTON_HEIGHT,
        radius=8,
        color=SWITCH_BUTTON_BORDER_COLOR
    )

    label: str = "ANA" if _mode == 0 else "DIG"
    display.draw_text(
        label,
        x=SWITCH_BUTTON_X + SWITCH_BUTTON_WIDTH // 2,
        y=SWITCH_BUTTON_Y + SWITCH_BUTTON_HEIGHT // 2,
        size=2,
        anchor="middle_center",
        color=0xFFFFFF,
        background_color=SWITCH_BUTTON_FILL_COLOR
    )


def update():
    global _previous_mode, _previous_second

    handle_touch() # handle touch at every update loop

    current_second: int = time.localtime()[5]

    if _previous_mode != _mode or _previous_second != current_second:
        _previous_mode = _mode
        _previous_second = current_second

        # redraw only if mode changed or second changed to avoid unnecessary redraws
        display.clear_canvas()

        if _mode == 0:
            draw_digital_clock()
        elif _mode == 1:
            draw_analog_clock()
        draw_battery()
        draw_switch_mode_button()

        display.flush_canvas()