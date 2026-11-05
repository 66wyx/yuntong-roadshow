"""240x320 pocket RID interface based on the repository radar/height mockups."""

import math
import time

import rid_decoder
import rid_fixtures
import rid_state
import ui_font
from ili9341 import ILI9341, rgb565


BG = rgb565(16, 24, 19)
INK = rgb565(233, 238, 230)
DIM = rgb565(161, 180, 163)
GRID = rgb565(55, 84, 67)
AXIS = rgb565(66, 96, 82)
ORANGE = rgb565(237, 128, 69)
OTHER = rgb565(129, 156, 133)
WHITE = rgb565(225, 238, 227)

RECEIVER_LAT = 22.6000
RECEIVER_LON = 114.3000
RECEIVER_ALT = 82.0


def text_right(fb, value, right, y, color, large=False):
    ui_font.draw(fb, value, right - ui_font.width(value, large), y, color, large)


def text_center(fb, value, center, y, color, large=False):
    ui_font.draw(
        fb, value, center - ui_font.width(value, large) // 2, y, color, large
    )


def dot(fb, x, y, radius, color):
    for row in range(-radius, radius + 1):
        span = int((radius * radius - row * row) ** 0.5)
        fb.fill_rect(x - span, y + row, span * 2 + 1, 1, color)


def upward_triangle(fb, x, y, color):
    for row in range(14):
        half = int(row * 0.45)
        fb.fill_rect(x - half, y + row, half * 2 + 1, 1, color)


def relative(target):
    if not target.get("position_valid"):
        return None
    mean_lat = math.radians((target["latitude"] + RECEIVER_LAT) * 0.5)
    east = (target["longitude"] - RECEIVER_LON) * 111320.0 * math.cos(mean_lat)
    north = (target["latitude"] - RECEIVER_LAT) * 110540.0
    distance = math.sqrt(east * east + north * north)
    bearing = (math.atan2(east, north) * 57.2957795 + 360.0) % 360.0
    altitude = target.get("altitude_geo_m")
    height = None if altitude is None else altitude - RECEIVER_ALT
    return east, north, distance, bearing, height


def draw_header(fb, title, target_count):
    ui_font.draw(fb, "云瞳 · RID", 10, 7, INK)
    text_right(fb, "演示 · 82%", 230, 7, INK)
    ui_font.draw(fb, title, 10, 29, INK)
    text_right(fb, "自动 · %d目标" % target_count, 230, 31, DIM)


def draw_footer(fb, target, relation, right_caption="范围 250m"):
    ui_font.draw(fb, "机头朝上", 10, 201, DIM)
    text_right(fb, right_caption, 230, 201, DIM)
    ui_font.draw(fb, target.get("uas_id", "UAV-01")[:12], 10, 219, INK)
    text_right(fb, "✓ 选定目标", 230, 221, ORANGE)
    ui_font.draw(fb, "水平距离", 10, 245, DIM)
    ui_font.draw(fb, "相对高度≈", 126, 245, DIM)
    horizontal = "--" if relation is None else "%d m" % int(relation[2] + 0.5)
    height_value = None if relation is None else relation[4]
    height = "--" if height_value is None else "%+.0f m" % height_value
    ui_font.draw(fb, horizontal, 10, 260, INK, large=True)
    ui_font.draw(fb, height, 126, 260, INK, large=True)
    fb.line(10, 292, 230, 292, AXIS)
    age = 0.8
    relationship = "右前方" if relation and relation[3] < 180 else "左前方"
    angle = 0 if relation is None else int(abs(relation[3] if relation[3] <= 180 else 360 - relation[3]) + 0.5)
    ui_font.draw(
        fb,
        "广播估算 · %.1f s · %s %d°" % (age, relationship, angle),
        10,
        301,
        DIM,
    )


def radar_page(fb, store, now_ms):
    fb.fill(BG)
    snapshots = store.snapshot(now_ms)
    draw_header(fb, "雷达俯视", len(snapshots))
    cx, cy = 120, 126
    for radius in (24, 48, 70):
        fb.ellipse(cx, cy, radius, radius, GRID)
    fb.line(50, cy, 190, cy, AXIS)
    fb.line(cx, 56, cx, 196, AXIS)
    ui_font.draw(fb, "N", 116, 53, DIM)
    upward_triangle(fb, 120, 117, WHITE)

    selected = store.get("astm_f3411:UAV-01")
    if selected is None and snapshots:
        selected = snapshots[0]
    selected_key = selected.get("key") if selected else None
    relation = relative(selected) if selected else None
    for target in snapshots:
        current = relative(target)
        if current is None or target.get("state") != "active":
            continue
        _, _, distance, bearing, _ = current
        scale = min(distance, 250.0) / 250.0 * 70.0
        x = int(cx + math.sin(math.radians(bearing)) * scale)
        y = int(cy - math.cos(math.radians(bearing)) * scale)
        selected_target = target.get("key") == selected_key
        if selected_target:
            fb.line(cx, cy, x, y, ORANGE)
            dot(fb, x, y, 5, ORANGE)
            ui_font.draw(fb, "01", x + 7, y - 8, ORANGE)
        else:
            dot(fb, x, y, 3, OTHER)
    if selected:
        draw_footer(fb, selected, relation)


def height_page(fb, store, now_ms):
    fb.fill(BG)
    snapshots = store.snapshot(now_ms)
    draw_header(fb, "高度示意", len(snapshots))
    selected = store.get("astm_f3411:UAV-01")
    if selected is None and snapshots:
        selected = snapshots[0]
    relation = relative(selected) if selected else None
    horizontal_angle = 0 if relation is None else relation[3]
    height_value = None if relation is None else relation[4]
    elevation = 0
    if relation and height_value is not None and relation[2] > 0:
        elevation = int(
            math.atan2(height_value, relation[2]) * 57.2957795 + 0.5
        )
    ui_font.draw(fb, "仰角约 %d°" % elevation, 18, 52, DIM)

    cx, cy = 120, 162
    fb.ellipse(cx, cy, 88, 29, GRID)
    fb.ellipse(cx, cy, 44, 15, GRID)
    fb.line(32, cy, 208, cy, AXIS)
    fb.line(cx, 72, cx, 193, AXIS)
    ui_font.draw(fb, "高度", 128, 68, DIM)
    dot(fb, cx, cy, 3, WHITE)
    if relation:
        east, north, distance, bearing, height = relation
        scale = min(distance, 250.0) / 250.0
        ground_x = int(cx + math.sin(math.radians(bearing)) * 42 * scale)
        ground_y = int(cy - math.cos(math.radians(bearing)) * 16 * scale)
        fb.line(cx, cy, ground_x, ground_y, WHITE)
        dot(fb, ground_x, ground_y, 4, ORANGE)
        if height is not None:
            top_y = int(ground_y - max(8, min(50, abs(height) * 0.7)))
            fb.line(ground_x, ground_y, ground_x, top_y, ORANGE)
            dot(fb, ground_x, top_y, 5, ORANGE)
            label = "%s · %+.0f m" % (
                selected.get("uas_id", "UAV")[:7],
                height,
            )
            label_width = ui_font.width(label)
            label_x = max(6, min(234 - label_width, ground_x - label_width // 2))
            label_y = top_y - 16
            fb.fill_rect(label_x - 2, label_y - 1, label_width + 4, 16, BG)
            ui_font.draw(fb, label, label_x, label_y, INK)
    draw_footer(fb, selected, relation, "纵向 ×2 示意")


def build_store():
    store = rid_state.TargetStore()
    for now_ms, latitude, longitude, altitude in (
        (0, 22.60138, 114.30045, 140.0),
        (1000, 22.60141, 114.30048, 142.0),
        (2000, 22.60143, 114.30050, 144.0),
    ):
        decoded = rid_decoder.decode_wifi_frame(
            rid_fixtures.astm_frame(
                uas_id="UAV-01",
                latitude=latitude,
                longitude=longitude,
                altitude_geo=altitude,
                height=62.0,
                counter=now_ms // 1000,
            ),
            rssi=-51,
            channel=6,
            now_ms=now_ms,
        )
        if decoded:
            store.apply(decoded[0], now_ms)
    for now_ms, latitude, longitude, altitude in (
        (0, 22.5992, 114.2992, 135.0),
        (1000, 22.5991, 114.2991, 136.0),
        (2000, 22.5990, 114.2990, 137.0),
    ):
        decoded = rid_decoder.decode_wifi_frame(
            rid_fixtures.gb46750_frame(
                uas_id="GB-DEMO",
                registration_id="UAS00002",
                latitude=latitude,
                longitude=longitude,
                altitude_geo=altitude,
                height=55.0,
            ),
            rssi=-63,
            channel=149,
            now_ms=now_ms,
        )
        if decoded:
            store.apply(decoded[0], now_ms)
    store.apply(
        {
            "protocol": "astm_f3411",
            "source_mac": "02:00:00:00:00:03",
            "uas_id": "IDENTITY-ONLY",
        },
        2000,
    )
    return store


def local_to_wgs84(x, y, z):
    latitude = RECEIVER_LAT + y / 110540.0
    longitude = RECEIVER_LON + x / (
        111320.0 * math.cos(math.radians(RECEIVER_LAT))
    )
    return latitude, longitude, RECEIVER_ALT + z


def build_motion_store(index):
    store = rid_state.TargetStore()
    now_ms = index * 1000 + 2000
    angle = math.radians((index * 18) % 360)
    x = 168.0 * math.sin(angle)
    y = 168.0 * math.cos(angle)
    z = 62.0 + 18.0 * math.sin(angle * 2.0)
    latitude, longitude, altitude = local_to_wgs84(x, y, z)
    decoded = rid_decoder.decode_wifi_frame(
        rid_fixtures.astm_frame(
            uas_id="UAV-01",
            latitude=latitude,
            longitude=longitude,
            altitude_geo=altitude,
            height=max(0.0, z),
            counter=index & 0xFF,
        ),
        rssi=-51,
        channel=6,
        now_ms=now_ms,
    )
    if decoded:
        store.apply(decoded[0], now_ms)

    x2 = -86.0 * math.cos(angle * 0.7)
    y2 = -52.0 + 28.0 * math.sin(angle * 0.7)
    latitude2, longitude2, altitude2 = local_to_wgs84(x2, y2, 34.0)
    decoded = rid_decoder.decode_wifi_frame(
        rid_fixtures.gb46750_frame(
            uas_id="GB-DEMO",
            registration_id="UAS00002",
            latitude=latitude2,
            longitude=longitude2,
            altitude_geo=altitude2,
            height=34.0,
        ),
        rssi=-63,
        channel=149,
        now_ms=now_ms,
    )
    if decoded:
        store.apply(decoded[0], now_ms)

    store.apply(
        {
            "protocol": "astm_f3411",
            "source_mac": "02:00:00:00:00:03",
            "uas_id": "IDENTITY-ONLY",
        },
        now_ms,
    )
    return store


def render_once():
    display = ILI9341()
    store = build_store()
    buffer, fb = display.new_frame()
    radar_page(fb, store, 2400)
    display.show(buffer)
    time.sleep_ms(4500)
    buffer, fb = display.new_frame()
    height_page(fb, store, 2400)
    display.show(buffer)
    time.sleep_ms(4500)
    buffer, fb = display.new_frame()
    radar_page(fb, store, 2400)
    display.show(buffer)
    print("pocket UI rendered from decoded replay data")


def main(loop=False, motion=False):
    if not loop:
        render_once()
        return
    if motion:
        display = ILI9341()
        index = 0
        while True:
            store = build_motion_store(index)
            buffer, fb = display.new_frame()
            if (index // 8) % 2 == 0:
                radar_page(fb, store, index * 1000 + 2000)
            else:
                height_page(fb, store, index * 1000 + 2000)
            display.show(buffer)
            time.sleep_ms(450)
            index += 1
        return
    display = ILI9341()
    store = build_store()
    while True:
        buffer, fb = display.new_frame()
        radar_page(fb, store, 2400)
        display.show(buffer)
        time.sleep_ms(4500)
        buffer, fb = display.new_frame()
        height_page(fb, store, 2400)
        display.show(buffer)
        time.sleep_ms(4500)


if __name__ == "__main__":
    main()
