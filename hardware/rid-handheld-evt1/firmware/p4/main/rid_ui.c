#include <math.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>

#include "rid_geo.h"
#include "rid_ui.h"

#define SCREEN_W 240
#define DEG 0.017453292519943295

/* Palette: graphite base, one warm accent reserved for the selected target. */
#define C_BG         GFX_RGB(9, 13, 18)
#define C_SURFACE    GFX_RGB(20, 26, 34)
#define C_CHIP       GFX_RGB(33, 42, 54)
#define C_GRID       GFX_RGB(38, 50, 63)
#define C_GRID_HI    GFX_RGB(58, 73, 89)
#define C_TEXT       GFX_RGB(232, 237, 242)
#define C_TEXT_2     GFX_RGB(140, 152, 166)
#define C_TEXT_3     GFX_RGB(88, 100, 114)
#define C_ACCENT     GFX_RGB(255, 159, 67)
#define C_LIVE       GFX_RGB(61, 214, 140)
#define C_TARGET     GFX_RGB(120, 160, 196)
#define C_STALE      GFX_RGB(84, 96, 110)

/* Layout. */
#define STATUS_BASELINE 18
#define RADAR_CX 120.0f
#define RADAR_CY 116.0f
#define RADAR_R 82.0f
#define CHART_LEFT 22.0f
#define CHART_RIGHT 218.0f
#define CHART_TOP 50.0f
#define CHART_GROUND 180.0f
#define FOOTNOTE_BASELINE 216
#define CARD_X 8
#define CARD_Y 224
#define CARD_W 224
#define CARD_H 90
#define CARD_PAD 12

typedef struct {
    const rid_target_snapshot_t *snapshot;
    rid_enu_t enu;
    double horizontal_m;
    double bearing_deg;
    bool has_position;
    bool fresh;
} target_view_t;

typedef struct {
    gfx_canvas_t *canvas;
    const rid_ui_frame_t *frame;
    target_view_t views[RID_RUNTIME_MAX_TARGETS];
    size_t count;
    size_t fresh_count;
    const target_view_t *selected;
    double range_m;
} ui_context_t;

/* ─── Text helpers ─── */

static int text(gfx_canvas_t *canvas,
                int x,
                int baseline,
                ui_font_id_t font,
                uint16_t color,
                const char *value)
{
    return gfx_text(canvas, x, baseline, font, color, value);
}

static int text_right(gfx_canvas_t *canvas,
                      int right,
                      int baseline,
                      ui_font_id_t font,
                      uint16_t color,
                      const char *value)
{
    const int width = gfx_text_width(font, value);
    gfx_text(canvas, right - width, baseline, font, color, value);
    return right - width;
}

/* Copies value into out, trimming with an ellipsis so it fits max_width. */
static void fit_text(char *out,
                     size_t out_size,
                     ui_font_id_t font,
                     const char *value,
                     int max_width)
{
    snprintf(out, out_size, "%s", value);
    if (gfx_text_width(font, out) <= max_width) {
        return;
    }
    size_t length = strlen(out);
    while (length > 0) {
        /* Step back over one whole UTF-8 sequence. */
        do {
            length--;
        } while (length > 0 && ((unsigned char)out[length] & 0xC0) == 0x80);
        char candidate[160];
        snprintf(candidate, sizeof(candidate), "%.*s…", (int)length, out);
        if (gfx_text_width(font, candidate) <= max_width) {
            snprintf(out, out_size, "%s", candidate);
            return;
        }
    }
    out[0] = '\0';
}

static void format_distance(char *value,
                            size_t value_size,
                            char *unit,
                            size_t unit_size,
                            double metres)
{
    if (metres >= 9999.5) {
        snprintf(value, value_size, "%.0f", metres / 1000.0);
        snprintf(unit, unit_size, "km");
    } else if (metres >= 1000.0) {
        snprintf(value, value_size, "%.2f", metres / 1000.0);
        snprintf(unit, unit_size, "km");
    } else {
        snprintf(value, value_size, "%.0f", metres);
        snprintf(unit, unit_size, "m");
    }
}

static void format_range(char *out, size_t out_size, double metres)
{
    if (metres >= 1000.0) {
        const double km = metres / 1000.0;
        if (fabs(km - floor(km)) < 0.05) {
            snprintf(out, out_size, "%.0f km", km);
        } else {
            snprintf(out, out_size, "%.1f km", km);
        }
    } else {
        snprintf(out, out_size, "%.0f m", metres);
    }
}

static void format_count(char *out, size_t out_size, uint32_t value)
{
    if (value >= 1000000u) {
        snprintf(out, out_size, "%.1fM", value / 1000000.0);
    } else if (value >= 1000u) {
        snprintf(out, out_size, "%.1fk", value / 1000.0);
    } else {
        snprintf(out, out_size, "%u", (unsigned)value);
    }
}

static void format_age(char *out, size_t out_size, uint64_t age_ms)
{
    if (age_ms < 60000u) {
        snprintf(out, out_size, "%.1f s", (double)age_ms / 1000.0);
    } else {
        snprintf(out, out_size, "%u s", (unsigned)(age_ms / 1000u));
    }
}

/* ─── View model ─── */

static const double RANGE_STEPS_M[] = {
    50, 100, 250, 500, 1000, 2500, 5000, 10000,
};
static const double HEIGHT_STEPS_M[] = {
    20, 50, 100, 200, 500, 1000, 2000,
};

static double pick_step(const double *steps, size_t count, double needed)
{
    for (size_t i = 0; i < count; i++) {
        if (steps[i] >= needed) {
            return steps[i];
        }
    }
    return steps[count - 1];
}

static void build_views(ui_context_t *ui)
{
    const rid_ui_frame_t *frame = ui->frame;
    ui->count = frame->target_count < RID_RUNTIME_MAX_TARGETS
                    ? frame->target_count
                    : RID_RUNTIME_MAX_TARGETS;
    ui->fresh_count = 0;
    double farthest = 0.0;
    for (size_t i = 0; i < ui->count; i++) {
        const rid_target_snapshot_t *snapshot = &frame->targets[i];
        target_view_t *view = &ui->views[i];
        memset(view, 0, sizeof(*view));
        view->snapshot = snapshot;
        view->has_position = snapshot->observation.position_valid &&
                             snapshot->last_position_ms != 0;
        if (!view->has_position) {
            continue;
        }
        view->enu = rid_geo_to_enu(&rid_receiver_anchor, &snapshot->observation);
        view->horizontal_m = rid_geo_horizontal_m(&view->enu);
        view->bearing_deg = rid_geo_bearing_deg(&view->enu);
        view->fresh = frame->now_ms >= snapshot->last_position_ms &&
                      frame->now_ms - snapshot->last_position_ms <=
                          RID_POSITION_STALE_MS;
        if (view->fresh) {
            ui->fresh_count++;
            if (view->horizontal_m > farthest) {
                farthest = view->horizontal_m;
            }
        }
    }

    /* Without input keys yet, follow the nearest live target. */
    ui->selected = NULL;
    for (size_t i = 0; i < ui->count; i++) {
        const target_view_t *view = &ui->views[i];
        if (view->fresh &&
            (!ui->selected || view->horizontal_m < ui->selected->horizontal_m)) {
            ui->selected = view;
        }
    }
    for (size_t i = 0; !ui->selected && i < ui->count; i++) {
        if (ui->views[i].has_position) {
            ui->selected = &ui->views[i];
        }
    }
    if (!ui->selected && ui->count) {
        ui->selected = &ui->views[0];
    }

    ui->range_m = pick_step(RANGE_STEPS_M,
                            sizeof(RANGE_STEPS_M) / sizeof(RANGE_STEPS_M[0]),
                            farthest > 0.0 ? farthest * 1.12 : 250.0);
}

static const char *target_name(const target_view_t *view)
{
    const rid_observation_t *observation = &view->snapshot->observation;
    if (observation->identity_valid && observation->uas_id[0]) {
        return observation->uas_id;
    }
    if (observation->identity_valid && observation->registration_id[0]) {
        return observation->registration_id;
    }
    return "未知身份";
}

static uint16_t target_color(const ui_context_t *ui, const target_view_t *view)
{
    if (view == ui->selected) {
        return C_ACCENT;
    }
    return view->fresh ? C_TARGET : C_STALE;
}

/* ─── Shared chrome ─── */

static void draw_status_bar(const ui_context_t *ui, const char *title)
{
    gfx_canvas_t *canvas = ui->canvas;
    const rid_ui_frame_t *frame = ui->frame;

    int x = 12 + text(canvas, 12, STATUS_BASELINE, UI_FONT_MEDIUM, C_TEXT, title);
    /* Page indicator: two dots, active one bright. */
    for (int page = 0; page < 2; page++) {
        gfx_fill_circle(canvas, (float)(x + 6 + page * 9), STATUS_BASELINE - 5.0f,
                        2.2f, page == (int)frame->page ? C_TEXT : C_TEXT_3, 255);
    }

    bool receiving = false;
    for (size_t i = 0; i < ui->count; i++) {
        if (frame->now_ms - ui->views[i].snapshot->last_seen_ms <=
            RID_POSITION_STALE_MS) {
            receiving = true;
        }
    }
    const char *state = receiving ? "接收中"
                        : frame->stats.mgmt_frames ? "监听中"
                                                   : "启动中";
    const uint16_t dot = receiving ? C_LIVE
                         : frame->stats.mgmt_frames ? C_TEXT_2
                                                    : C_TEXT_3;
    char label[64];
    snprintf(label, sizeof(label), "%s · CH%u", state, frame->stats.channel);
    const int left = text_right(canvas, SCREEN_W - 12, STATUS_BASELINE,
                                UI_FONT_SMALL, C_TEXT_2, label);
    gfx_fill_circle(canvas, (float)(left - 8), STATUS_BASELINE - 4.5f, 3.0f, dot, 255);
}

static void draw_metric(gfx_canvas_t *canvas,
                        int x,
                        const char *label,
                        const char *value,
                        const char *unit,
                        uint16_t value_color)
{
    text(canvas, x, CARD_Y + 41, UI_FONT_SMALL, C_TEXT_3, label);
    const int width = text(canvas, x, CARD_Y + 66, UI_FONT_LARGE, value_color, value);
    if (unit && unit[0]) {
        text(canvas, x + width + 2, CARD_Y + 66, UI_FONT_SMALL, C_TEXT_2, unit);
    }
}

static void draw_chip(gfx_canvas_t *canvas,
                      int right,
                      int baseline,
                      const char *label,
                      uint16_t fill,
                      uint16_t color)
{
    const int width = gfx_text_width(UI_FONT_SMALL, label) + 10;
    gfx_fill_round_rect(canvas, right - width, baseline - 12, width, 16, 4, fill);
    text(canvas, right - width + 5, baseline, UI_FONT_SMALL, color, label);
}

static void draw_empty_card(const ui_context_t *ui)
{
    gfx_canvas_t *canvas = ui->canvas;
    const rid_ui_stats_t *stats = &ui->frame->stats;
    const int x = CARD_X + CARD_PAD;
    text(canvas, x, CARD_Y + 24, UI_FONT_MEDIUM, C_TEXT, "等待 RID 广播");

    char mgmt[16];
    char rid[16];
    format_count(mgmt, sizeof(mgmt), stats->mgmt_frames);
    format_count(rid, sizeof(rid), stats->rid_frames);
    char line[128];
    snprintf(line, sizeof(line), "管理帧 %s · RID 帧 %s", mgmt, rid);
    text(canvas, x, CARD_Y + 50, UI_FONT_SMALL, C_TEXT_2, line);
    snprintf(line, sizeof(line), "信道 %u · 无人机广播将自动显示", stats->channel);
    text(canvas, x, CARD_Y + 72, UI_FONT_SMALL, C_TEXT_3, line);
}

static void draw_target_card(const ui_context_t *ui, bool height_page)
{
    gfx_canvas_t *canvas = ui->canvas;
    const target_view_t *view = ui->selected;
    const rid_target_snapshot_t *snapshot = view->snapshot;
    const rid_observation_t *observation = &snapshot->observation;
    const uint64_t now_ms = ui->frame->now_ms;
    const int x = CARD_X + CARD_PAD;
    const int right = CARD_X + CARD_W - CARD_PAD;

    /* Header: identity on the left, protocol and age chips on the right. */
    const char *protocol =
        observation->vendor_type == RID_VENDOR_TYPE_GB ? "GB" : "ASTM";
    const uint64_t reference_ms =
        view->has_position ? snapshot->last_position_ms : snapshot->last_seen_ms;
    char age[16];
    format_age(age, sizeof(age), now_ms - reference_ms);
    const int age_width = gfx_text_width(UI_FONT_SMALL, age);
    const int protocol_right = right - age_width - 8;
    text_right(canvas, right, CARD_Y + 23, UI_FONT_SMALL,
               view->fresh ? C_TEXT_2 : C_TEXT_3, age);
    draw_chip(canvas, protocol_right, CARD_Y + 23, protocol, C_CHIP, C_TEXT_2);
    const int protocol_width = gfx_text_width(UI_FONT_SMALL, protocol) + 10;

    char name[48];
    fit_text(name, sizeof(name), UI_FONT_MEDIUM, target_name(view),
             protocol_right - protocol_width - 8 - x);
    gfx_fill_circle(canvas, (float)x + 3.0f, CARD_Y + 18.0f, 3.0f,
                    view->fresh ? C_ACCENT : C_STALE, 255);
    text(canvas, x + 12, CARD_Y + 24, UI_FONT_MEDIUM,
         view->fresh ? C_TEXT : C_TEXT_2, name);

    /* Metrics: distance, relative height, then bearing or elevation. */
    char distance[24] = "—";
    char distance_unit[8] = "";
    char height[24] = "—";
    char angle[24] = "—";
    if (view->fresh) {
        format_distance(distance, sizeof(distance),
                        distance_unit, sizeof(distance_unit), view->horizontal_m);
        if (view->enu.up_valid) {
            snprintf(height, sizeof(height), "%+.0f", view->enu.up_m);
        }
        if (height_page) {
            if (view->enu.up_valid) {
                snprintf(angle, sizeof(angle), "%.0f°",
                         atan2(view->enu.up_m, view->horizontal_m) / DEG);
            }
        } else {
            snprintf(angle, sizeof(angle), "%03.0f°", view->bearing_deg);
        }
    }
    const uint16_t value_color = view->fresh ? C_TEXT : C_TEXT_3;
    draw_metric(canvas, x, "距离", distance, distance_unit, value_color);
    draw_metric(canvas, x + 74, "相对高度", height,
                strcmp(height, "—") ? "m" : "", value_color);
    draw_metric(canvas, x + 152, height_page ? "仰角" : "方位", angle, "",
                value_color);

    /* Footer: kinematics while live, otherwise why the numbers are missing. */
    char footer[160];
    if (!view->has_position) {
        snprintf(footer, sizeof(footer), "已识别身份 · 等待位置报文");
    } else if (!view->fresh) {
        char stale[16];
        format_age(stale, sizeof(stale), now_ms - snapshot->last_position_ms);
        snprintf(footer, sizeof(footer), "位置已过期 · %s 前", stale);
    } else {
        char speed[24] = "—";
        char track[16] = "—";
        if (observation->speed_valid) {
            snprintf(speed, sizeof(speed), "%.1f m/s", observation->speed_horizontal_mps);
        }
        if (observation->direction_valid) {
            snprintf(track, sizeof(track), "%03.0f°", observation->direction_deg);
        }
        snprintf(footer, sizeof(footer), "地速 %s · 航迹 %s · %d dBm",
                 speed, track, snapshot->rssi);
    }
    char fitted[160];
    fit_text(fitted, sizeof(fitted), UI_FONT_SMALL, footer, right - x);
    text(canvas, x, CARD_Y + CARD_H - 8, UI_FONT_SMALL, C_TEXT_3, fitted);
}

static void draw_card(const ui_context_t *ui, bool height_page)
{
    gfx_fill_round_rect(ui->canvas, CARD_X, CARD_Y, CARD_W, CARD_H, 10, C_SURFACE);
    if (ui->selected) {
        draw_target_card(ui, height_page);
    } else {
        draw_empty_card(ui);
    }
}

static void draw_footnote(const ui_context_t *ui, const char *right_label)
{
    char count[64];
    snprintf(count, sizeof(count), "%u 个目标 · %u 实时",
             (unsigned)ui->count, (unsigned)ui->fresh_count);
    text(ui->canvas, 12, FOOTNOTE_BASELINE, UI_FONT_SMALL, C_TEXT_3, count);
    text_right(ui->canvas, SCREEN_W - 12, FOOTNOTE_BASELINE, UI_FONT_SMALL,
               C_TEXT_3, right_label);
}

/* Short label beside a marker, kept inside the given horizontal bounds. */
static void draw_marker_label(gfx_canvas_t *canvas,
                              float x,
                              float y,
                              const char *value,
                              int left_limit,
                              int right_limit)
{
    char label[64];
    fit_text(label, sizeof(label), UI_FONT_SMALL, value, 80);
    const int width = gfx_text_width(UI_FONT_SMALL, label);
    int lx = (int)(x + 12.0f);
    if (lx + width > right_limit) {
        lx = (int)(x - 12.0f) - width;
    }
    if (lx < left_limit) {
        lx = left_limit;
    }
    text(canvas, lx, (int)(y - 6.0f), UI_FONT_SMALL, C_ACCENT, label);
}

/* ─── Radar (plan view, north up) ─── */

static void radar_point(const ui_context_t *ui,
                        const target_view_t *view,
                        float *x,
                        float *y,
                        bool *clamped)
{
    double scale = view->horizontal_m / ui->range_m;
    *clamped = scale > 1.0;
    if (*clamped) {
        scale = 1.0;
    }
    const double radians = view->bearing_deg * DEG;
    *x = RADAR_CX + (float)(sin(radians) * scale * RADAR_R);
    *y = RADAR_CY - (float)(cos(radians) * scale * RADAR_R);
}

static void draw_heading(gfx_canvas_t *canvas,
                         float x,
                         float y,
                         const rid_observation_t *observation,
                         float length,
                         float width,
                         uint16_t color)
{
    if (!observation->direction_valid ||
        !observation->speed_valid ||
        observation->speed_horizontal_mps < 0.5) {
        return;
    }
    const double radians = observation->direction_deg * DEG;
    gfx_line(canvas, x, y,
             x + (float)(sin(radians) * length),
             y - (float)(cos(radians) * length),
             width, color, 220);
}

static void draw_radar_grid(const ui_context_t *ui)
{
    gfx_canvas_t *canvas = ui->canvas;
    gfx_ring(canvas, RADAR_CX, RADAR_CY, RADAR_R, 1.0f, C_GRID_HI, 255);
    gfx_ring(canvas, RADAR_CX, RADAR_CY, RADAR_R * 0.5f, 1.0f, C_GRID, 255);
    gfx_dashed_line(canvas, RADAR_CX - RADAR_R, RADAR_CY, RADAR_CX + RADAR_R,
                    RADAR_CY, 1.0f, 2.0f, 3.0f, C_GRID, 255);
    gfx_dashed_line(canvas, RADAR_CX, RADAR_CY - RADAR_R, RADAR_CX,
                    RADAR_CY + RADAR_R, 1.0f, 2.0f, 3.0f, C_GRID, 255);

    /* Bezel ticks every 30 degrees, longer at the cardinals. */
    for (int degrees = 0; degrees < 360; degrees += 30) {
        const bool cardinal = degrees % 90 == 0;
        const float inner = RADAR_R - (cardinal ? 6.0f : 3.5f);
        const double radians = degrees * DEG;
        gfx_line(canvas,
                 RADAR_CX + (float)(sin(radians) * inner),
                 RADAR_CY - (float)(cos(radians) * inner),
                 RADAR_CX + (float)(sin(radians) * RADAR_R),
                 RADAR_CY - (float)(cos(radians) * RADAR_R),
                 1.0f, cardinal ? C_TEXT_2 : C_GRID_HI, 255);
    }
    const int north_width = gfx_text_width(UI_FONT_SMALL, "N");
    text(canvas, (int)RADAR_CX - north_width / 2, (int)(RADAR_CY - RADAR_R) + 19,
         UI_FONT_SMALL, C_TEXT_2, "N");

    char label[64];
    format_range(label, sizeof(label), ui->range_m * 0.5);
    text(canvas, (int)(RADAR_CX + RADAR_R * 0.5f) + 3, (int)RADAR_CY + 13,
         UI_FONT_SMALL, C_TEXT_3, label);

    /* Receiver at the center. */
    gfx_ring(canvas, RADAR_CX, RADAR_CY, 6.0f, 1.0f, C_TEXT_2, 140);
    gfx_fill_circle(canvas, RADAR_CX, RADAR_CY, 2.6f, C_TEXT, 255);
}

static void draw_radar_target(const ui_context_t *ui, const target_view_t *view)
{
    gfx_canvas_t *canvas = ui->canvas;
    float x;
    float y;
    bool clamped;
    radar_point(ui, view, &x, &y, &clamped);
    const uint16_t color = target_color(ui, view);

    if (view != ui->selected) {
        if (view->fresh && !clamped) {
            draw_heading(canvas, x, y, &view->snapshot->observation, 9.0f, 1.4f, color);
            gfx_fill_circle(canvas, x, y, 3.5f, color, 255);
        } else {
            gfx_ring(canvas, x, y, 3.5f, 1.3f, color, 255);
        }
        return;
    }

    if (!view->fresh) {
        gfx_ring(canvas, x, y, 5.0f, 1.5f, C_STALE, 255);
        return;
    }
    gfx_dashed_line(canvas, RADAR_CX, RADAR_CY, x, y, 1.0f, 3.0f, 3.0f, C_ACCENT, 120);
    gfx_fill_circle(canvas, x, y, 11.0f, C_ACCENT, 34);
    gfx_ring(canvas, x, y, 11.0f, 1.0f, C_ACCENT, 110);
    draw_heading(canvas, x, y, &view->snapshot->observation, 17.0f, 2.0f, C_ACCENT);
    if (clamped) {
        gfx_ring(canvas, x, y, 4.5f, 2.0f, C_ACCENT, 255);
    } else {
        gfx_fill_circle(canvas, x, y, 5.0f, C_ACCENT, 255);
    }
    draw_marker_label(canvas, x, y, target_name(view), 8, SCREEN_W - 8);
}

static void render_radar(const ui_context_t *ui)
{
    draw_status_bar(ui, "俯视");
    draw_radar_grid(ui);
    /* Background targets first so the selected one is never covered. */
    for (size_t i = 0; i < ui->count; i++) {
        if (ui->views[i].has_position && &ui->views[i] != ui->selected) {
            draw_radar_target(ui, &ui->views[i]);
        }
    }
    if (ui->selected && ui->selected->has_position) {
        draw_radar_target(ui, ui->selected);
    }
    char range[24];
    char label[64];
    format_range(range, sizeof(range), ui->range_m);
    snprintf(label, sizeof(label), "北向上 · %s", range);
    draw_footnote(ui, label);
    draw_card(ui, false);
}

/* ─── Height (side profile) ─── */

static float profile_x(const ui_context_t *ui, double horizontal_m)
{
    double ratio = horizontal_m / ui->range_m;
    if (ratio > 1.0) {
        ratio = 1.0;
    }
    return CHART_LEFT + (float)ratio * (CHART_RIGHT - CHART_LEFT);
}

static float profile_y(double up_m, double height_range_m)
{
    double ratio = up_m / height_range_m;
    if (ratio > 1.0) ratio = 1.0;
    if (ratio < -0.12) ratio = -0.12;
    return CHART_GROUND - (float)ratio * (CHART_GROUND - CHART_TOP);
}

static void render_height(const ui_context_t *ui)
{
    gfx_canvas_t *canvas = ui->canvas;
    draw_status_bar(ui, "高度");

    double highest = 0.0;
    for (size_t i = 0; i < ui->count; i++) {
        const target_view_t *view = &ui->views[i];
        if (view->fresh && view->enu.up_valid && fabs(view->enu.up_m) > highest) {
            highest = fabs(view->enu.up_m);
        }
    }
    const double height_range = pick_step(
        HEIGHT_STEPS_M, sizeof(HEIGHT_STEPS_M) / sizeof(HEIGHT_STEPS_M[0]),
        highest > 0.0 ? highest * 1.15 : 100.0);

    /* Grid: two height bands and two distance ticks, all labelled. */
    char label[64];
    for (int step = 1; step <= 2; step++) {
        const double metres = height_range * step / 2.0;
        const float y = profile_y(metres, height_range);
        gfx_dashed_line(canvas, CHART_LEFT, y, CHART_RIGHT, y, 1.0f, 2.0f, 3.0f,
                        C_GRID, 255);
        format_range(label, sizeof(label), metres);
        /* Left edge: target labels sit to the right of their markers. */
        text(canvas, (int)CHART_LEFT - 10, (int)y - 4, UI_FONT_SMALL, C_TEXT_3, label);
    }
    for (int step = 1; step <= 2; step++) {
        const float x = profile_x(ui, ui->range_m * step / 2.0);
        gfx_line(canvas, x, CHART_GROUND, x, CHART_GROUND + 4.0f, 1.0f, C_GRID_HI, 255);
        format_range(label, sizeof(label), ui->range_m * step / 2.0);
        const int width = gfx_text_width(UI_FONT_SMALL, label);
        text(canvas, step == 2 ? (int)x - width : (int)x - width / 2,
             (int)CHART_GROUND + 18, UI_FONT_SMALL, C_TEXT_3, label);
    }
    gfx_line(canvas, CHART_LEFT, CHART_GROUND, CHART_RIGHT, CHART_GROUND, 1.0f,
             C_GRID_HI, 255);
    text(canvas, (int)CHART_LEFT - 10, (int)CHART_GROUND + 18, UI_FONT_SMALL,
         C_TEXT_3, "本机");
    gfx_fill_circle(canvas, CHART_LEFT, CHART_GROUND, 3.0f, C_TEXT, 255);

    for (size_t i = 0; i < ui->count; i++) {
        const target_view_t *view = &ui->views[i];
        if (!view->has_position || view == ui->selected) {
            continue;
        }
        const float x = profile_x(ui, view->horizontal_m);
        const uint16_t color = target_color(ui, view);
        if (view->fresh && view->enu.up_valid) {
            gfx_fill_circle(canvas, x, profile_y(view->enu.up_m, height_range),
                            3.5f, color, 255);
        } else {
            gfx_ring(canvas, x, CHART_GROUND, 3.5f, 1.3f, color, 255);
        }
    }

    const target_view_t *selected = ui->selected;
    if (selected && selected->fresh) {
        const float x = profile_x(ui, selected->horizontal_m);
        if (selected->enu.up_valid) {
            const float y = profile_y(selected->enu.up_m, height_range);
            gfx_dashed_line(canvas, x, y, x, CHART_GROUND, 1.0f, 2.0f, 2.0f,
                            C_ACCENT, 150);
            gfx_line(canvas, CHART_LEFT, CHART_GROUND, x, y, 1.2f, C_ACCENT, 170);
            gfx_fill_circle(canvas, x, CHART_GROUND, 2.0f, C_ACCENT, 200);
            const float screen_angle =
                atan2f(CHART_GROUND - y, x - CHART_LEFT) * 57.29578f;
            gfx_arc(canvas, CHART_LEFT, CHART_GROUND, 24.0f, 1.2f, 0.0f,
                    screen_angle, C_ACCENT, 200);
            gfx_fill_circle(canvas, x, y, 11.0f, C_ACCENT, 34);
            gfx_ring(canvas, x, y, 11.0f, 1.0f, C_ACCENT, 110);
            gfx_fill_circle(canvas, x, y, 5.0f, C_ACCENT, 255);
            char value[40];
            snprintf(value, sizeof(value), "%+.0f m", selected->enu.up_m);
            draw_marker_label(canvas, x, y, value, 8, SCREEN_W - 8);
        } else {
            gfx_ring(canvas, x, CHART_GROUND, 5.0f, 2.0f, C_ACCENT, 255);
            draw_marker_label(canvas, x, CHART_GROUND, "高度未知", 8, SCREEN_W - 8);
        }
    }

    /* Vertical exaggeration must always be visible when present. */
    const double vertical_scale =
        ((CHART_GROUND - CHART_TOP) / height_range) /
        ((CHART_RIGHT - CHART_LEFT) / ui->range_m);
    if (fabs(vertical_scale - 1.0) < 0.1) {
        snprintf(label, sizeof(label), "纵横等比");
    } else if (vertical_scale >= 9.5) {
        snprintf(label, sizeof(label), "纵轴 ×%.0f", vertical_scale);
    } else {
        snprintf(label, sizeof(label), "纵轴 ×%.1f", vertical_scale);
    }
    draw_footnote(ui, label);
    draw_card(ui, true);
}

void rid_ui_draw(gfx_canvas_t *canvas, const rid_ui_frame_t *frame)
{
    ui_context_t ui = {
        .canvas = canvas,
        .frame = frame,
    };
    build_views(&ui);
    gfx_clear(canvas, C_BG);
    if (frame->page == RID_UI_HEIGHT) {
        render_height(&ui);
    } else {
        render_radar(&ui);
    }
}
