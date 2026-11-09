#include <math.h>
#include <stdio.h>
#include <string.h>

#include "esp_log.h"

#include "ili9341.h"
#include "rid_runtime.h"
#include "rid_ui.h"
#include "ui_font.h"

#define RECEIVER_LAT 22.6000
#define RECEIVER_LON 114.3000
#define RADAR_RANGE_M 250.0f

#define COLOR_BG      ili9341_rgb565(16, 24, 19)
#define COLOR_INK     ili9341_rgb565(233, 238, 230)
#define COLOR_DIM     ili9341_rgb565(161, 180, 163)
#define COLOR_GRID    ili9341_rgb565(55, 84, 67)
#define COLOR_AXIS    ili9341_rgb565(66, 96, 82)
#define COLOR_ORANGE  ili9341_rgb565(237, 128, 69)
#define COLOR_OTHER   ili9341_rgb565(129, 156, 133)
#define COLOR_WHITE   ili9341_rgb565(225, 238, 227)

typedef struct {
    uint16_t color;
} text_context_t;

typedef struct {
    float east;
    float north;
    float distance;
    float bearing;
    float height;
    bool valid;
} relative_t;

static const char *TAG = "rid_ui";

static void text_plot(int x, int y, void *context)
{
    const text_context_t *text = (const text_context_t *)context;
    ili9341_pixel(x, y, text->color);
}

static void draw_text(const char *text, int x, int y, uint16_t color, int large)
{
    text_context_t context = {.color = color};
    ui_font_draw(text_plot, &context, text, x, y, color, large);
}

static void draw_text_right(const char *text,
                            int right,
                            int y,
                            uint16_t color,
                            int large)
{
    draw_text(text, right - ui_font_width(text, large), y, color, large);
}

static void draw_text_center(const char *text,
                             int center,
                             int y,
                             uint16_t color,
                             int large)
{
    draw_text(text,
              center - ui_font_width(text, large) / 2,
              y,
              color,
              large);
}

static int round_int(float value)
{
    return (int)(value >= 0.0f ? value + 0.5f : value - 0.5f);
}

static void draw_upward_triangle(int x, int y, uint16_t color)
{
    for (int row = 0; row < 14; row++) {
        int half = row * 45 / 100;
        ili9341_fill_rect(x - half, y + row, half * 2 + 1, 1, color);
    }
}

static float age_seconds(const rid_target_snapshot_t *target, uint64_t now_ms)
{
    if (!target->last_position_ms) {
        return 0.0f;
    }
    return (float)(now_ms - target->last_position_ms) / 1000.0f;
}

static bool position_is_active(const rid_target_snapshot_t *target,
                               uint64_t now_ms)
{
    return target->observation.position_valid &&
           target->last_position_ms &&
           now_ms - target->last_position_ms <= RID_POSITION_STALE_MS;
}

static relative_t calculate_relative(const rid_target_snapshot_t *target)
{
    relative_t result = {0};
    if (!target || !target->observation.position_valid) {
        return result;
    }
    const double mean_latitude =
        (target->observation.latitude + RECEIVER_LAT) * 0.5 * M_PI / 180.0;
    result.east = (float)(
        (target->observation.longitude - RECEIVER_LON) *
        111320.0 * cos(mean_latitude));
    result.north = (float)(
        (target->observation.latitude - RECEIVER_LAT) * 110540.0);
    result.distance = sqrtf(
        result.east * result.east + result.north * result.north);
    result.bearing = atan2f(result.east, result.north) * 57.2957795f;
    if (result.bearing < 0.0f) {
        result.bearing += 360.0f;
    }
    result.height = (float)target->observation.altitude_geo_m;
    result.valid = true;
    return result;
}

static const rid_target_snapshot_t *select_position_target(
    const rid_target_snapshot_t *targets,
    size_t count,
    uint64_t now_ms)
{
    for (size_t i = 0; i < count; i++) {
        if (position_is_active(&targets[i], now_ms)) {
            return &targets[i];
        }
    }
    for (size_t i = 0; i < count; i++) {
        if (targets[i].observation.position_valid) {
            return &targets[i];
        }
    }
    return count ? &targets[0] : NULL;
}

static const char *target_id(const rid_target_snapshot_t *target)
{
    if (target && target->observation.identity_valid &&
        target->observation.uas_id[0]) {
        static char shortened[13];
        snprintf(shortened, sizeof(shortened), "%.12s", target->observation.uas_id);
        return shortened;
    }
    return "RID TARGET";
}

static void draw_header(const char *title,
                        size_t target_count,
                        size_t position_count)
{
    char status[32];
    snprintf(status,
             sizeof(status),
             "真实 · %u目标",
             (unsigned)target_count);
    draw_text("云瞳 · RID", 10, 7, COLOR_INK, 0);
    draw_text_right(status, 230, 7, COLOR_INK, 0);
    draw_text(title, 10, 29, COLOR_INK, 0);
    snprintf(status,
             sizeof(status),
             "CH6 · %u定位",
             (unsigned)position_count);
    draw_text_right(status, 230, 31, COLOR_DIM, 0);
}

static void draw_footer(const rid_target_snapshot_t *target,
                        const relative_t *relation,
                        uint64_t now_ms,
                        const char *range_caption)
{
    draw_text("机头朝上", 10, 201, COLOR_DIM, 0);
    draw_text_right(range_caption, 230, 201, COLOR_DIM, 0);

    if (!target) {
        draw_text("RID 广播", 10, 219, COLOR_INK, 0);
        draw_text_right("等待中", 230, 221, COLOR_ORANGE, 0);
        draw_text("水平距离", 10, 245, COLOR_DIM, 0);
        draw_text("相对高度≈", 126, 245, COLOR_DIM, 0);
        draw_text("--", 10, 260, COLOR_INK, 1);
        draw_text("--", 126, 260, COLOR_INK, 1);
        ili9341_line(10, 292, 230, 292, COLOR_AXIS);
        draw_text("真实空口 · 信道6", 10, 301, COLOR_DIM, 0);
        return;
    }

    draw_text(target_id(target), 10, 219, COLOR_INK, 0);
    draw_text_right("✓ 选定目标", 230, 221, COLOR_ORANGE, 0);
    draw_text("水平距离", 10, 245, COLOR_DIM, 0);
    draw_text("相对高度≈", 126, 245, COLOR_DIM, 0);

    char horizontal[24] = "--";
    char vertical[24] = "--";
    if (relation && relation->valid) {
        snprintf(horizontal, sizeof(horizontal), "%d m", round_int(relation->distance));
        snprintf(vertical, sizeof(vertical), "%+.0f m", relation->height);
    }
    draw_text(horizontal, 10, 260, COLOR_INK, 1);
    draw_text(vertical, 126, 260, COLOR_INK, 1);
    ili9341_line(10, 292, 230, 292, COLOR_AXIS);

    if (relation && relation->valid) {
        const char *side = relation->bearing < 180.0f ? "右前方" : "左前方";
        int angle = round_int(
            relation->bearing <= 180.0f
                ? relation->bearing
                : 360.0f - relation->bearing);
        char caption[64];
        snprintf(caption,
                 sizeof(caption),
                 "广播估算 · %.1f s · %s %d°",
                 age_seconds(target, now_ms),
                 side,
                 angle);
        draw_text(caption, 10, 301, COLOR_DIM, 0);
    } else {
        draw_text("RID 已识别 · 等待位置", 10, 301, COLOR_DIM, 0);
    }
}

static void render_radar(const rid_target_snapshot_t *targets,
                         size_t count,
                         size_t position_count,
                         uint64_t now_ms)
{
    draw_header("雷达俯视", count, position_count);
    const int cx = 120;
    const int cy = 126;
    ili9341_ellipse(cx, cy, 24, 24, COLOR_GRID);
    ili9341_ellipse(cx, cy, 48, 48, COLOR_GRID);
    ili9341_ellipse(cx, cy, 70, 70, COLOR_GRID);
    ili9341_line(50, cy, 190, cy, COLOR_AXIS);
    ili9341_line(cx, 56, cx, 196, COLOR_AXIS);
    draw_text("N", 116, 53, COLOR_DIM, 0);
    draw_upward_triangle(cx, 117, COLOR_WHITE);

    const rid_target_snapshot_t *selected =
        select_position_target(targets, count, now_ms);
    relative_t selected_relation = calculate_relative(selected);
    const uint8_t *selected_mac =
        selected ? selected->observation.source_mac : NULL;

    for (size_t i = 0; i < count; i++) {
        if (!position_is_active(&targets[i], now_ms)) {
            continue;
        }
        relative_t relation = calculate_relative(&targets[i]);
        float scale = relation.distance < RADAR_RANGE_M
                          ? relation.distance / RADAR_RANGE_M * 70.0f
                          : 70.0f;
        float radians = relation.bearing * (float)M_PI / 180.0f;
        int x = cx + round_int(sinf(radians) * scale);
        int y = cy - round_int(cosf(radians) * scale);
        bool is_selected =
            selected_mac &&
            memcmp(selected_mac, targets[i].observation.source_mac, 6) == 0;
        if (is_selected) {
            ili9341_line(cx, cy, x, y, COLOR_ORANGE);
            ili9341_fill_circle(x, y, 5, COLOR_ORANGE);
            draw_text("01", x + 7, y - 8, COLOR_ORANGE, 0);
        } else {
            ili9341_fill_circle(x, y, 3, COLOR_OTHER);
        }
    }

    if (selected && selected_relation.valid) {
        char xyz[48];
        snprintf(xyz,
                 sizeof(xyz),
                 "XYZ %+.0f, %+.0f, %+.0f",
                 selected_relation.east,
                 selected_relation.north,
                 selected_relation.height);
        draw_text(xyz, 10, 185, COLOR_DIM, 0);
    }
    draw_footer(selected, &selected_relation, now_ms, "范围 250m");
}

static void render_height(const rid_target_snapshot_t *targets,
                          size_t count,
                          size_t position_count,
                          uint64_t now_ms)
{
    draw_header("高度示意", count, position_count);
    const rid_target_snapshot_t *selected =
        select_position_target(targets, count, now_ms);
    relative_t relation = calculate_relative(selected);
    int elevation = 0;
    if (relation.valid && relation.distance > 1.0f) {
        elevation = round_int(
            atan2f(relation.height, relation.distance) * 57.2957795f);
    }

    char caption[32];
    snprintf(caption, sizeof(caption), "仰角约 %d°", elevation);
    draw_text(caption, 18, 52, COLOR_DIM, 0);

    const int cx = 120;
    const int cy = 162;
    ili9341_ellipse(cx, cy, 88, 29, COLOR_GRID);
    ili9341_ellipse(cx, cy, 44, 15, COLOR_GRID);
    ili9341_line(32, cy, 208, cy, COLOR_AXIS);
    ili9341_line(cx, 72, cx, 193, COLOR_AXIS);
    draw_text("高度", 128, 68, COLOR_DIM, 0);
    ili9341_fill_circle(cx, cy, 3, COLOR_WHITE);

    if (relation.valid) {
        float scale = relation.distance < RADAR_RANGE_M
                          ? relation.distance / RADAR_RANGE_M
                          : 1.0f;
        float radians = relation.bearing * (float)M_PI / 180.0f;
        int ground_x = cx + round_int(sinf(radians) * 42.0f * scale);
        int ground_y = cy - round_int(cosf(radians) * 16.0f * scale);
        ili9341_line(cx, cy, ground_x, ground_y, COLOR_WHITE);
        ili9341_fill_circle(ground_x, ground_y, 4, COLOR_ORANGE);
        float rise = fabsf(relation.height) * 0.7f;
        if (rise < 8.0f) rise = 8.0f;
        if (rise > 50.0f) rise = 50.0f;
        int top_y = ground_y -
                    round_int(relation.height >= 0.0f ? rise : -rise);
        ili9341_line(ground_x, ground_y, ground_x, top_y, COLOR_ORANGE);
        ili9341_fill_circle(ground_x, top_y, 5, COLOR_ORANGE);

        char label[48];
        snprintf(label,
                 sizeof(label),
                 "%.7s · %+.0f m",
                 target_id(selected),
                 relation.height);
        int label_width = ui_font_width(label, 0);
        int label_x = ground_x - label_width / 2;
        if (label_x < 6) label_x = 6;
        if (label_x + label_width > 234) label_x = 234 - label_width;
        int label_y = top_y - 16;
        ili9341_fill_rect(label_x - 2, label_y - 1, label_width + 4, 16, COLOR_BG);
        draw_text(label, label_x, label_y, COLOR_INK, 0);
    }
    draw_footer(selected, &relation, now_ms, "纵向 ×2 示意");
}

bool rid_ui_init(void)
{
    if (!ili9341_init()) {
        ESP_LOGE(TAG, "Display initialization failed");
        return false;
    }
    ili9341_clear(COLOR_BG);
    draw_text_center("云瞳 · RID", 120, 116, COLOR_INK, 0);
    draw_text_center("真实空口接收", 120, 144, COLOR_DIM, 0);
    ili9341_flush();
    return true;
}

void rid_ui_render(rid_ui_page_t page, uint64_t now_ms)
{
    rid_target_snapshot_t targets[RID_RUNTIME_MAX_TARGETS];
    size_t count = rid_runtime_snapshot(now_ms, targets, RID_RUNTIME_MAX_TARGETS);
    size_t position_count = 0;
    for (size_t i = 0; i < count; i++) {
        if (position_is_active(&targets[i], now_ms)) {
            position_count++;
        }
    }

    ili9341_clear(COLOR_BG);
    if (page == RID_UI_HEIGHT) {
        render_height(targets, count, position_count, now_ms);
    } else {
        render_radar(targets, count, position_count, now_ms);
    }
    ili9341_flush();
}
