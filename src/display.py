import M5 # type: ignore


_lcd: M5.Lcd = M5.Lcd


def show_text(text: str, size: int = 2, color: int = 0xFFFFFF, background_color: int = 0x000000, x: int = 20, y: int = 20):
    _lcd.setTextSize(size)
    _lcd.setTextColor(color, background_color)
    _lcd.drawString(text, x, y)
