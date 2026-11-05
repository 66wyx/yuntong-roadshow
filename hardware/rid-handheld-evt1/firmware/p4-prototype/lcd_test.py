"""EVT0 display and touch smoke test. Run with: import lcd_test"""

import time

from ft6336 import FT6336
from ili9341 import ILI9341, rgb565


BLACK = rgb565(0, 0, 0)
WHITE = rgb565(255, 255, 255)
GREY = rgb565(70, 74, 78)
PALE = rgb565(225, 224, 216)
ORANGE = rgb565(224, 84, 28)
GREEN = rgb565(0, 145, 90)
BLUE = rgb565(30, 70, 140)


def main():
    display = ILI9341()
    buffer, fb = display.new_frame()
    fb.fill(PALE)
    fb.fill_rect(0, 0, display.width, 42, BLACK)
    fb.text("YUNTONG / EVT0", 12, 14, WHITE)
    fb.text("DISPLAY + TOUCH TEST", 12, 62, GREY)

    for i, color in enumerate((BLACK, WHITE, ORANGE, GREEN, BLUE)):
        fb.fill_rect(12 + i * 44, 90, 38, 38, color)

    fb.rect(8, 155, display.width - 16, 104, BLACK)
    fb.text("TARGET 01", 20, 172, BLACK)
    fb.text("LAB-TEST-001", 20, 194, GREY)
    fb.text("168 m / +62 m", 20, 216, ORANGE)
    fb.text("AGE 0.8 s", 20, 238, GREY)
    fb.text("Touch screen to test", 20, 284, BLACK)
    display.show(buffer)

    touch = FT6336()
    found = touch.scan()
    print("I2C scan:", [hex(address) for address in found])
    if touch.ADDRESS in found:
        print("FT6336G ID:", touch.check_id())
    else:
        print("FT6336G not found; UI remains visible but touch is not validated")

    deadline = time.ticks_add(time.ticks_ms(), 30_000)
    last_message = None
    while time.ticks_diff(deadline, time.ticks_ms()) > 0:
        points = touch.read() if touch.ADDRESS in found else []
        message = str(points)
        if points and message != last_message:
            print("touch:", message)
            last_message = message
        time.sleep_ms(20)
    print("EVT0 display/touch test complete")


main()

