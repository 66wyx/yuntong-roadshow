"""Decode generated RID beacon frames, update state, and render touchless UI."""

import math
import time

import rid_decoder
import rid_fixtures
import rid_state
from ili9341 import ILI9341, rgb565


BLACK = rgb565(18, 20, 22)
INK = rgb565(44, 48, 50)
GREY = rgb565(120, 124, 125)
PALE = rgb565(232, 230, 220)
WHITE = rgb565(255, 255, 255)
ORANGE = rgb565(224, 84, 28)
GREEN = rgb565(44, 145, 92)
RED = rgb565(190, 52, 46)
BLUE = rgb565(36, 88, 160)
LINE = rgb565(185, 184, 176)

RECEIVER_LAT = 22.5998
RECEIVER_LON = 114.3001
RECEIVER_ALT = 82.0


def header(fb, title):
    fb.fill_rect(0, 0, 240, 32, BLACK)
    fb.text(title, 8, 11, WHITE)
    fb.text("REPLAY", 191, 11, ORANGE)


def footer(fb, text):
    fb.fill_rect(0, 294, 240, 26, BLACK)
    fb.text(text[:29], 8, 303, WHITE)


def fmt(value, decimals):
    if value is None:
        return "--"
    return ("%." + str(decimals) + "f") % value


def relative_position(target):
    if not target.get("position_valid"):
        return None
    mean_lat = math.radians((target["latitude"] + RECEIVER_LAT) * 0.5)
    east = (target["longitude"] - RECEIVER_LON) * 111320.0 * math.cos(mean_lat)
    north = (target["latitude"] - RECEIVER_LAT) * 110540.0
    altitude = target.get("altitude_geo_m")
    up = None if altitude is None else altitude - RECEIVER_ALT
    return east, north, math.sqrt(east * east + north * north), up


def page_status(display, store, now_ms, frames):
    buffer, fb = display.new_frame()
    fb.fill(PALE)
    header(fb, "RID RECEIVER")
    snapshots = store.snapshot(now_ms)
    active = sum(1 for target in snapshots if target["state"] == "active")
    stale = sum(1 for target in snapshots if target["state"] == "stale")
    expired = sum(1 for target in snapshots if target["state"] == "expired")
    gb_count = sum(
        1 for target in snapshots if target["protocol"] == "gb46750_2025"
    )
    astm_count = sum(1 for target in snapshots if target["protocol"] == "astm_f3411")

    fb.text("SOURCE", 10, 46, GREY)
    fb.text("GENERATED FIXTURE", 10, 62, ORANGE)
    fb.rect(8, 82, 224, 102, LINE)
    fb.text("TARGETS", 20, 94, GREY)
    fb.text(str(len(snapshots)), 184, 94, INK)
    fb.text("ACTIVE", 20, 114, GREY)
    fb.text(str(active), 184, 114, GREEN)
    fb.text("STALE", 20, 134, GREY)
    fb.text(str(stale), 184, 134, ORANGE)
    fb.text("EXPIRED", 20, 154, GREY)
    fb.text(str(expired), 184, 154, RED)
    fb.text("ASTM", 10, 198, GREY)
    fb.text(str(astm_count), 72, 198, INK)
    fb.text("GB46750", 112, 198, GREY)
    fb.text(str(gb_count), 196, 198, INK)
    fb.text("FRAMES", 10, 224, GREY)
    fb.text(str(frames), 72, 224, INK)
    fb.text("DECODE OK", 112, 224, GREY)
    fb.text(str(frames), 204, 224, GREEN)
    fb.text("POSITION STALE", 10, 254, GREY)
    fb.text("3 s", 122, 254, INK)
    fb.text("HIDE AFTER", 10, 274, GREY)
    fb.text("10 s", 118, 274, INK)
    footer(fb, "SIMULATED DATA - NOT LIVE RF")
    display.show(buffer)


def page_list(display, store, now_ms):
    buffer, fb = display.new_frame()
    fb.fill(PALE)
    header(fb, "TARGET LIST")
    snapshots = store.snapshot(now_ms)
    for index, target in enumerate(snapshots[:3]):
        top = 42 + index * 82
        state = target["state"]
        color = {
            "active": GREEN,
            "stale": ORANGE,
            "expired": RED,
            "identity_only": GREY,
        }[state]
        fb.rect(8, top, 224, 70, LINE)
        fb.fill_rect(8, top, 5, 70, color)
        fb.text((target.get("uas_id") or target.get("source_mac") or "UNKNOWN")[:20], 20, top + 7, INK)
        protocol = "GB46750" if target["protocol"] == "gb46750_2025" else "ASTM"
        fb.text(protocol + "  " + state.upper(), 20, top + 25, color)
        position_age = target["position_age_ms"]
        age_text = "--" if position_age is None else fmt(position_age / 1000.0, 1) + " s"
        fb.text("POS AGE " + age_text, 20, top + 44, GREY)
        rssi = target.get("rssi_dbm")
        fb.text("RSSI " + ("--" if rssi is None else str(rssi)), 144, top + 44, GREY)
    footer(fb, "POSITION AGE IS INDEPENDENT")
    display.show(buffer)


def page_detail(display, target, now_ms):
    buffer, fb = display.new_frame()
    fb.fill(PALE)
    header(fb, "TARGET DETAIL")
    if target is None:
        fb.text("NO TARGET", 12, 52, RED)
    else:
        fb.text((target.get("uas_id") or "UNKNOWN")[:27], 10, 44, INK)
        protocol = "GB46750-2025" if target["protocol"] == "gb46750_2025" else "ASTM F3411"
        fb.text(protocol, 10, 62, BLUE)
        fb.text("LAT", 10, 88, GREY)
        fb.text(fmt(target.get("latitude"), 7), 78, 88, INK)
        fb.text("LON", 10, 108, GREY)
        fb.text(fmt(target.get("longitude"), 7), 78, 108, INK)
        fb.text("GEO ALT", 10, 136, GREY)
        fb.text(fmt(target.get("altitude_geo_m"), 1) + " m", 104, 136, INK)
        fb.text("HEIGHT", 10, 156, GREY)
        fb.text(fmt(target.get("height_m"), 1) + " m", 104, 156, INK)
        fb.text("SPEED", 10, 176, GREY)
        fb.text(fmt(target.get("speed_horizontal_mps"), 1) + " m/s", 104, 176, INK)
        fb.text("TRACK", 10, 196, GREY)
        fb.text(fmt(target.get("direction_deg"), 1) + " deg", 104, 196, INK)
        fb.text("GCS LAT", 10, 226, GREY)
        fb.text(fmt(target.get("operator_latitude"), 6), 104, 226, INK)
        fb.text("GCS LON", 10, 246, GREY)
        fb.text(fmt(target.get("operator_longitude"), 6), 104, 246, INK)
        position_age = now_ms - target["last_position_ms"]
        fb.text("POS AGE", 10, 268, GREY)
        fb.text(fmt(position_age / 1000.0, 1) + " s", 104, 268, INK)
    footer(fb, "BROADCAST POSITION - UNVERIFIED")
    display.show(buffer)


def page_radar(display, store, now_ms):
    buffer, fb = display.new_frame()
    fb.fill(PALE)
    header(fb, "RADAR / REPLAY")
    cx, cy = 120, 184
    for radius in (36, 72, 108):
        fb.ellipse(cx, cy, radius, radius, LINE)
    fb.line(cx, 56, cx, 292, LINE)
    fb.line(10, cy, 230, cy, LINE)
    fb.text("N", 116, 40, INK)
    fb.text("300m", 8, 166, GREY)
    positioned = [
        target
        for target in store.snapshot(now_ms)
        if target["state"] == "active" and relative_position(target)
    ]
    if not positioned:
        fb.text("NO ACTIVE POSITION", 38, 276, RED)
    for target in positioned[:4]:
        east, north, distance, _ = relative_position(target)
        scale = min(105.0 / max(distance, 1.0), 1.0)
        px = int(cx + east * scale)
        py = int(cy - north * scale)
        fb.fill_rect(px - 3, py - 3, 7, 7, ORANGE)
        label = "GB" if target["protocol"] == "gb46750_2025" else "ASTM"
        fb.text(label, px + 6, py - 3, INK)
        fb.text(str(int(distance + 0.5)) + "m", px + 6, py + 7, GREY)
    fb.fill_rect(cx - 2, cy - 2, 5, 5, GREEN)
    footer(fb, "GENERATED REPLAY / NORTH UP")
    display.show(buffer)


def build_store():
    store = rid_state.TargetStore()
    frames = 0
    samples = (
        (0, 22.6000, 114.3000, 125.0, 62.0, -51),
        (1000, 22.6004, 114.3003, 127.0, 64.0, -52),
        (2000, 22.6008, 114.3006, 129.0, 66.0, -53),
    )
    for sample in samples:
        now, lat, lon, altitude, height, rssi = sample
        frames_decoded = rid_decoder.decode_wifi_frame(
            rid_fixtures.astm_frame(
                latitude=lat,
                longitude=lon,
                altitude_geo=altitude,
                height=height,
                counter=now // 1000,
            ),
            rssi=rssi,
            channel=6,
            now_ms=now,
        )
        if frames_decoded:
            store.apply(frames_decoded[0], now)
            frames += 1
    samples = (
        (0, 22.5987, 114.3012, 155.0, 75.0, -62),
        (1000, 22.5986, 114.3011, 156.0, 76.0, -63),
        (2000, 22.5985, 114.3010, 157.0, 77.0, -64),
    )
    for sample in samples:
        now, lat, lon, altitude, height, rssi = sample
        frames_decoded = rid_decoder.decode_wifi_frame(
            rid_fixtures.gb46750_frame(
                latitude=lat,
                longitude=lon,
                altitude_geo=altitude,
                height=height,
            ),
            rssi=rssi,
            channel=149,
            now_ms=now,
        )
        if frames_decoded:
            store.apply(frames_decoded[0], now)
            frames += 1
    return store, frames


def main():
    display = ILI9341()
    store, frames = build_store()
    now_ms = 2400
    page_status(display, store, now_ms, frames)
    time.sleep_ms(2500)
    page_list(display, store, now_ms)
    time.sleep_ms(2500)
    snapshots = store.snapshot(now_ms)
    primary = next(
        (target for target in snapshots if target["protocol"] == "gb46750_2025"),
        snapshots[0] if snapshots else None,
    )
    page_detail(display, primary, now_ms)
    time.sleep_ms(3000)
    page_radar(display, store, now_ms)
    time.sleep_ms(3000)
    page_status(display, store, 6500, frames)
    time.sleep_ms(3000)
    page_status(display, store, 12500, frames)
    print("RID replay demo complete: %d decoded frames, %d targets" % (frames, len(store.targets)))


main()
