"""Display-only EVT0 smoke test. The final frame remains on the panel."""

from st7789 import ST7789, rgb565


def run():
    display = ST7789()
    buffer, fb = display.new_frame()
    black = rgb565(0, 0, 0)
    white = rgb565(255, 255, 255)
    red = rgb565(220, 30, 30)
    green = rgb565(20, 160, 80)
    blue = rgb565(30, 80, 200)
    yellow = rgb565(245, 190, 20)
    grey = rgb565(180, 180, 170)

    fb.fill(white)
    fb.fill_rect(0, 0, 240, 60, black)
    fb.text("EVT0 DISPLAY OK", 20, 25, white)
    fb.fill_rect(0, 60, 60, 180, red)
    fb.fill_rect(60, 60, 60, 180, green)
    fb.fill_rect(120, 60, 60, 180, blue)
    fb.fill_rect(180, 60, 60, 180, yellow)
    fb.fill_rect(12, 258, 216, 48, grey)
    fb.text("ST7789  240 x 320", 34, 278, black)
    display.show(buffer)
    print("display frame sent; it should remain visible")


run()
