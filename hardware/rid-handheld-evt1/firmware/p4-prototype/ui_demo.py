"""Touchless UI readability test for the EVT0 RID validation rig."""

import time

from ili9341 import ILI9341, rgb565


BLACK = rgb565(18, 20, 22)
INK = rgb565(44, 48, 50)
GREY = rgb565(120, 124, 125)
PALE = rgb565(232, 230, 220)
WHITE = rgb565(255, 255, 255)
ORANGE = rgb565(224, 84, 28)
GREEN = rgb565(44, 145, 92)
RED = rgb565(190, 52, 46)
LINE = rgb565(185, 184, 176)


def header(fb, title, page):
    fb.fill_rect(0, 0, 240, 34, BLACK)
    fb.text(title, 10, 12, WHITE)
    fb.text("%d/3" % page, 216, 12, WHITE)


def footer(fb, text):
    fb.fill_rect(0, 292, 240, 28, BLACK)
    fb.text(text, 10, 302, WHITE)


def page_status(display, buffer, fb):
    fb.fill(PALE)
    header(fb, "RECEIVER STATUS", 1)
    fb.text("MODE", 12, 52, GREY)
    fb.text("DEMO / NO RF", 12, 70, RED)
    fb.rect(10, 96, 220, 72, LINE)
    fb.text("2.4 GHz", 22, 108, INK)
    fb.text("5.8 GHz", 22, 134, INK)
    fb.text("not tested", 122, 108, GREY)
    fb.text("not available", 122, 134, GREY)
    fb.text("RAW FRAMES", 12, 188, GREY)
    fb.text("0", 12, 208, INK)
    fb.text("ACTIVE TARGETS", 12, 246, GREY)
    fb.text("0", 12, 266, INK)
    fb.text("SERIAL + DISPLAY READY", 12, 278, GREEN)
    footer(fb, "SIMULATED DATA MUST BE LABELED")
    display.show(buffer)


def page_targets(display, buffer, fb):
    fb.fill(PALE)
    header(fb, "TARGET LIST", 2)
    rows = (
        ("LAB-TEST-001", "GB46750", "168 m  +62 m", GREEN),
        ("DEMO-A2", "ASTM", "245 m  +38 m", ORANGE),
        ("NO POSITION", "UNKNOWN", "identity only", GREY),
    )
    for i, (identity, protocol, detail, color) in enumerate(rows):
        top = 48 + i * 76
        fb.rect(8, top, 224, 64, LINE)
        fb.fill_rect(8, top, 5, 64, color)
        fb.text(identity, 20, top + 8, INK)
        fb.text(protocol, 20, top + 26, GREY)
        fb.text(detail, 20, top + 44, INK)
    footer(fb, "DEMO LABELS - NOT REAL TARGETS")
    display.show(buffer)


def page_radar(display, buffer, fb):
    fb.fill(PALE)
    header(fb, "RADAR / DEMO", 3)
    cx, cy = 120, 174
    for radius in (35, 70, 105):
        fb.ellipse(cx, cy, radius, radius, LINE)
    fb.line(cx, 62, cx, 286, LINE)
    fb.line(18, cy, 222, cy, LINE)
    fb.text("N", 116, 43, INK)
    fb.fill_rect(cx - 3, cy - 3, 6, 6, GREEN)
    fb.fill_rect(146, 120, 8, 8, ORANGE)
    fb.text("168m", 158, 116, INK)
    fb.fill_rect(74, 194, 8, 8, RED)
    fb.text("245m", 38, 208, INK)
    fb.text("TARGET 1 SELECTED", 10, 38, ORANGE)
    footer(fb, "SIMULATED POSITION / NORTH UP")
    display.show(buffer)


def main():
    display = ILI9341()
    for page in range(2):
        buffer, fb = display.new_frame()
        if page == 0:
            fb.fill(PALE)
            header(fb, "UI VALIDATION", 1)
            fb.text("ILI9341 DISPLAY OK", 16, 62, GREEN)
            fb.text("240 x 320 / RGB565", 16, 84, INK)
            fb.fill_rect(16, 116, 208, 5, BLACK)
            fb.text("Status", 16, 142, INK)
            fb.text("Targets", 16, 166, INK)
            fb.text("Radar", 16, 190, INK)
            fb.text("Height", 16, 214, INK)
            fb.rect(8, 132, 224, 108, LINE)
            fb.text("Touch deferred", 16, 264, RED)
            footer(fb, "AUTO SCREEN - NO TOUCH REQUIRED")
            display.show(buffer)
            time.sleep_ms(2500)
        if page == 1:
            page_status(display, buffer, fb)
            time.sleep_ms(2500)
        buffer, fb = display.new_frame()
        page_targets(display, buffer, fb)
        time.sleep_ms(3000)
        buffer, fb = display.new_frame()
        page_radar(display, buffer, fb)
        time.sleep_ms(3000)
    print("UI demo complete; radar page remains visible")


main()
