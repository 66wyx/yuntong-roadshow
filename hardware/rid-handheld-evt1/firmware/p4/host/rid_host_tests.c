/*
 * Host unit tests for the portable P4 receiver modules.
 *
 *   rid_host_tests
 *
 * Exit status is non-zero on the first failing assertion.
 */

#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "rid_decoder.h"
#include "rid_geo.h"
#include "rid_gfx.h"
#include "rid_runtime.h"
#include "rid_ui.h"
#include "ui_font.h"

static int s_failures;

#define CHECK(condition)                                                   \
    do {                                                                   \
        if (!(condition)) {                                                \
            fprintf(stderr, "FAIL %s:%d %s\n", __FILE__, __LINE__, #condition); \
            s_failures++;                                                  \
        }                                                                  \
    } while (0)

#define CHECK_NEAR(actual, expected, tolerance) \
    CHECK(fabs((double)(actual) - (double)(expected)) <= (tolerance))

/* ─── Frame builders ─── */

static size_t beacon_header(uint8_t *frame)
{
    memset(frame, 0, 36);
    frame[0] = 0x80; /* beacon */
    memset(frame + 4, 0xFF, 6);
    const uint8_t mac[6] = {0x02, 0, 0, 0, 0, 0x01};
    memcpy(frame + 10, mac, 6);
    memcpy(frame + 16, mac, 6);
    return 36;
}

static void put_u16(uint8_t *p, unsigned value)
{
    p[0] = (uint8_t)value;
    p[1] = (uint8_t)(value >> 8);
}

static void put_i32(uint8_t *p, long value)
{
    const uint32_t raw = (uint32_t)value;
    p[0] = (uint8_t)raw;
    p[1] = (uint8_t)(raw >> 8);
    p[2] = (uint8_t)(raw >> 16);
    p[3] = (uint8_t)(raw >> 24);
}

static unsigned astm_altitude(double metres)
{
    return (unsigned)lround((metres + 1000.0) * 2.0);
}

/* ASTM message pack: Basic ID + Location + Operator ID. */
static size_t astm_frame(uint8_t *frame,
                         uint8_t direction_raw,
                         bool east_west,
                         bool with_basic_id)
{
    size_t length = beacon_header(frame);
    uint8_t messages[3][25];
    memset(messages, 0, sizeof(messages));
    size_t count = 0;

    if (with_basic_id) {
        messages[count][0] = 0x02;
        messages[count][1] = 0x12;
        memcpy(messages[count] + 2, "UAS-SERIAL-01", 13);
        count++;
    }
    uint8_t *location = messages[count++];
    location[0] = 0x12;
    location[1] = (uint8_t)(0x20 | (east_west ? 0x02 : 0x00));
    location[2] = direction_raw;
    location[3] = 40;  /* 10 m/s */
    location[4] = 4;
    put_i32(location + 5, 226010000L);   /* 22.6010000 */
    put_i32(location + 9, 1143005000L);  /* 114.3005000 */
    put_u16(location + 13, astm_altitude(120.0));
    put_u16(location + 15, astm_altitude(140.0));
    put_u16(location + 17, astm_altitude(60.0));

    uint8_t *operator_id = messages[count++];
    operator_id[0] = 0x52;
    memcpy(operator_id + 2, "PILOT-007", 9);

    const size_t payload = 1 + 3 + 25 * count;
    frame[length++] = 221;
    frame[length++] = (uint8_t)(4 + payload);
    frame[length++] = 0xFA;
    frame[length++] = 0x0B;
    frame[length++] = 0xBC;
    frame[length++] = 0x0D;
    frame[length++] = 0x00; /* message counter */
    frame[length++] = 0xF2;
    frame[length++] = 25;
    frame[length++] = (uint8_t)count;
    memcpy(frame + length, messages, 25 * count);
    return length + 25 * count;
}

/* ─── Decoder ─── */

static void test_astm_direction_west(void)
{
    uint8_t frame[256];
    rid_observation_t o;
    /* 270 deg is encoded as 90 with the E/W flag; uint8 math gave 14 deg. */
    CHECK(rid_decode_frame(frame, astm_frame(frame, 90, true, true), -50, 6, &o));
    CHECK(o.direction_valid);
    CHECK_NEAR(o.direction_deg, 270.0, 1e-9);

    CHECK(rid_decode_frame(frame, astm_frame(frame, 179, true, true), -50, 6, &o));
    CHECK_NEAR(o.direction_deg, 359.0, 1e-9);

    CHECK(rid_decode_frame(frame, astm_frame(frame, 90, false, true), -50, 6, &o));
    CHECK_NEAR(o.direction_deg, 90.0, 1e-9);

    /* 361 = unknown: raw 181 with the flag. */
    CHECK(rid_decode_frame(frame, astm_frame(frame, 181, true, true), -50, 6, &o));
    CHECK(!o.direction_valid);
}

static void test_astm_operator_is_not_aircraft_id(void)
{
    uint8_t frame[256];
    rid_observation_t o;
    CHECK(rid_decode_frame(frame, astm_frame(frame, 0, false, false), -50, 6, &o));
    CHECK(!o.identity_valid);
    CHECK(o.uas_id[0] == '\0');
    CHECK(strcmp(o.operator_id, "PILOT-007") == 0);

    CHECK(rid_decode_frame(frame, astm_frame(frame, 0, false, true), -50, 6, &o));
    CHECK(o.identity_valid);
    CHECK(strcmp(o.uas_id, "UAS-SERIAL-01") == 0);
    CHECK(strcmp(o.operator_id, "PILOT-007") == 0);
}

static void test_astm_altitudes(void)
{
    uint8_t frame[256];
    rid_observation_t o;
    CHECK(rid_decode_frame(frame, astm_frame(frame, 0, false, true), -50, 6, &o));
    CHECK(o.position_valid);
    CHECK(o.altitude_geo_valid);
    CHECK_NEAR(o.altitude_geo_m, 140.0, 1e-9);
    CHECK(o.height_valid);
    CHECK_NEAR(o.height_m, 60.0, 1e-9);
    CHECK(o.speed_valid);
    CHECK_NEAR(o.speed_horizontal_mps, 10.0, 1e-9);
}

/* ─── Geometry ─── */

static void test_geo_relative_height_uses_receiver_datum(void)
{
    const rid_geo_anchor_t anchor = {22.6, 114.3, 30.0};
    rid_observation_t o;
    memset(&o, 0, sizeof(o));
    o.latitude = 22.6 + 100.0 / 110540.0;
    o.longitude = 114.3;
    o.altitude_geo_m = 92.0;
    o.altitude_geo_valid = true;
    o.height_m = 500.0; /* above take-off: must not leak into "relative height" */
    o.height_valid = true;
    const rid_enu_t enu = rid_geo_to_enu(&anchor, &o);
    CHECK(enu.up_valid);
    CHECK_NEAR(enu.up_m, 62.0, 1e-9);
    CHECK_NEAR(enu.north_m, 100.0, 1e-6);
    CHECK_NEAR(rid_geo_bearing_deg(&enu), 0.0, 1e-6);

    o.altitude_geo_valid = false;
    CHECK(!rid_geo_to_enu(&anchor, &o).up_valid);
}

static void test_geo_bearing_quadrants(void)
{
    const rid_enu_t east = {100, 0, 0, true};
    const rid_enu_t south = {0, -100, 0, true};
    const rid_enu_t west = {-100, 0, 0, true};
    CHECK_NEAR(rid_geo_bearing_deg(&east), 90.0, 1e-9);
    CHECK_NEAR(rid_geo_bearing_deg(&south), 180.0, 1e-9);
    CHECK_NEAR(rid_geo_bearing_deg(&west), 270.0, 1e-9);
    CHECK_NEAR(rid_geo_horizontal_m(&east), 100.0, 1e-9);
}

/* ─── Graphics ─── */

#define CANVAS_W 240
#define CANVAS_H 320
static uint8_t s_pixels[CANVAS_W * CANVAS_H * 2];

static void lit_extent(const gfx_canvas_t *canvas,
                       int *min_x,
                       int *max_x,
                       int *min_y,
                       int *max_y)
{
    *min_x = *min_y = 1 << 30;
    *max_x = *max_y = -1;
    for (int y = 0; y < canvas->height; y++) {
        for (int x = 0; x < canvas->width; x++) {
            if (gfx_get_pixel(canvas, x, y)) {
                if (x < *min_x) *min_x = x;
                if (x > *max_x) *max_x = x;
                if (y < *min_y) *min_y = y;
                if (y > *max_y) *max_y = y;
            }
        }
    }
}

static void test_ring_is_round(void)
{
    gfx_canvas_t canvas = {s_pixels, CANVAS_W, CANVAS_H};
    gfx_clear(&canvas, 0);
    /* The old ellipse spanned 24..35 px for r=24; a ring must stay within r ± width. */
    gfx_ring(&canvas, 120.0f, 160.0f, 70.0f, 1.0f, 0xFFFF, 255);
    int min_x, max_x, min_y, max_y;
    lit_extent(&canvas, &min_x, &max_x, &min_y, &max_y);
    CHECK(min_x >= 120 - 72 && max_x <= 120 + 72);
    CHECK(min_y >= 160 - 72 && max_y <= 160 + 72);
    CHECK(abs((max_x - min_x) - (max_y - min_y)) <= 1);
    for (int y = 0; y < CANVAS_H; y++) {
        for (int x = 0; x < CANVAS_W; x++) {
            if (gfx_get_pixel(&canvas, x, y)) {
                const double r = hypot(x - 120.0, y - 160.0);
                CHECK(r > 68.5 && r < 71.5);
            }
        }
    }
}

static void test_primitives_clip(void)
{
    gfx_canvas_t canvas = {s_pixels, CANVAS_W, CANVAS_H};
    gfx_clear(&canvas, 0);
    gfx_fill_circle(&canvas, -5.0f, -5.0f, 20.0f, 0xFFFF, 255);
    gfx_line(&canvas, -100, -100, 400, 500, 3.0f, 0xFFFF, 255);
    gfx_ring(&canvas, 230.0f, 310.0f, 40.0f, 2.0f, 0xFFFF, 255);
    gfx_fill_round_rect(&canvas, 200, 300, 100, 100, 10, 0xFFFF);
    gfx_text(&canvas, 230, 330, UI_FONT_LARGE, 0xFFFF, "8888");
    CHECK(gfx_get_pixel(&canvas, 0, 0) == 0xFFFF);
}

/* ─── Fonts ─── */

static void test_font_covers_ui_text(void)
{
    static const char *const samples[] = {
        "等待 RID 广播", "接收中 · CH6", "监听中", "启动中",
        "未知身份", "已识别身份 · 等待位置报文", "位置已过期 · 7.0 s 前",
        "地速 7.4 m/s · 航迹 248° · -58 dBm", "北向上 · 250 m", "纵轴 ×2",
        "纵横等比", "高度未知", "相对高度", "距离", "方位", "仰角", "俯视", "本机",
        "管理帧 1.8M · RID 帧 0", "3 个目标 · 2 实时", "1.25 km",
        /* Received identities may use any printable ASCII. */
        " !\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`",
        "abcdefghijklmnopqrstuvwxyz{|}~",
    };
    for (size_t i = 0; i < sizeof(samples) / sizeof(samples[0]); i++) {
        const char *cursor = samples[i];
        while (*cursor) {
            const uint32_t codepoint = ui_font_next_codepoint(&cursor);
            const bool present = ui_font_glyph(UI_FONT_SMALL, codepoint) != NULL;
            if (!present) {
                fprintf(stderr, "missing small glyph U+%04X in \"%s\"\n",
                        (unsigned)codepoint, samples[i]);
            }
            CHECK(present);
        }
    }
    const char *digits = "+-0123456789.—°";
    while (*digits) {
        CHECK(ui_font_glyph(UI_FONT_LARGE, ui_font_next_codepoint(&digits)) != NULL);
    }
}

/* ─── UI ─── */

static void test_ui_renders_all_states(void)
{
    gfx_canvas_t canvas = {s_pixels, CANVAS_W, CANVAS_H};
    rid_target_snapshot_t target;
    memset(&target, 0, sizeof(target));
    target.observation.decoded = true;
    target.observation.identity_valid = true;
    strcpy(target.observation.uas_id, "A-VERY-LONG-SERIALID");
    target.observation.position_valid = true;
    target.observation.latitude = 22.6 + 5000.0 / 110540.0; /* beyond range steps */
    target.observation.longitude = 114.3;
    target.observation.altitude_geo_valid = false;
    target.last_position_ms = 1000;
    target.last_seen_ms = 1000;

    for (int page = 0; page < 2; page++) {
        rid_ui_frame_t frame = {
            .page = (rid_ui_page_t)page,
            .now_ms = 1500,
            .stats = {.channel = 6},
            .targets = &target,
            .target_count = 1,
        };
        rid_ui_draw(&canvas, &frame);
        frame.now_ms = 20000;
        rid_ui_draw(&canvas, &frame);
        frame.target_count = 0;
        rid_ui_draw(&canvas, &frame);
    }
    CHECK(true);
}

int main(void)
{
    test_astm_direction_west();
    test_astm_operator_is_not_aircraft_id();
    test_astm_altitudes();
    test_geo_relative_height_uses_receiver_datum();
    test_geo_bearing_quadrants();
    test_ring_is_round();
    test_primitives_clip();
    test_font_covers_ui_text();
    test_ui_renders_all_states();
    if (s_failures) {
        fprintf(stderr, "%d check(s) failed\n", s_failures);
        return 1;
    }
    printf("P4 host tests passed\n");
    return 0;
}
