#include <math.h>
#include <stdbool.h>
#include <stddef.h>

#include "rid_gfx.h"

static float clampf(float value, float low, float high)
{
    return value < low ? low : (value > high ? high : value);
}

static int floor_int(float value)
{
    return (int)floorf(value);
}

static int ceil_int(float value)
{
    return (int)ceilf(value);
}

static bool clip_box(const gfx_canvas_t *canvas,
                     int *x0,
                     int *y0,
                     int *x1,
                     int *y1)
{
    if (*x0 < 0) *x0 = 0;
    if (*y0 < 0) *y0 = 0;
    if (*x1 > canvas->width - 1) *x1 = canvas->width - 1;
    if (*y1 > canvas->height - 1) *y1 = canvas->height - 1;
    return *x0 <= *x1 && *y0 <= *y1;
}

static uint8_t coverage_alpha(float coverage, uint8_t alpha)
{
    return (uint8_t)(clampf(coverage, 0.0f, 1.0f) * (float)alpha + 0.5f);
}

uint16_t gfx_blend(uint16_t background, uint16_t foreground, uint8_t alpha)
{
    if (alpha == 0) {
        return background;
    }
    if (alpha == 255) {
        return foreground;
    }
    const unsigned inverse = 255u - alpha;
    const unsigned r = (((foreground >> 11) & 0x1F) * alpha +
                        ((background >> 11) & 0x1F) * inverse + 127) / 255;
    const unsigned g = (((foreground >> 5) & 0x3F) * alpha +
                        ((background >> 5) & 0x3F) * inverse + 127) / 255;
    const unsigned b = ((foreground & 0x1F) * alpha +
                        (background & 0x1F) * inverse + 127) / 255;
    return (uint16_t)((r << 11) | (g << 5) | b);
}

static void put_pixel(gfx_canvas_t *canvas, int x, int y, uint16_t color)
{
    uint8_t *pixel = canvas->pixels + ((size_t)y * canvas->width + x) * 2;
    pixel[0] = (uint8_t)(color >> 8);
    pixel[1] = (uint8_t)color;
}

uint16_t gfx_get_pixel(const gfx_canvas_t *canvas, int x, int y)
{
    if (x < 0 || y < 0 || x >= canvas->width || y >= canvas->height) {
        return 0;
    }
    const uint8_t *pixel =
        canvas->pixels + ((size_t)y * canvas->width + x) * 2;
    return (uint16_t)((pixel[0] << 8) | pixel[1]);
}

void gfx_blend_pixel(gfx_canvas_t *canvas,
                     int x,
                     int y,
                     uint16_t color,
                     uint8_t alpha)
{
    if (alpha == 0 || x < 0 || y < 0 ||
        x >= canvas->width || y >= canvas->height) {
        return;
    }
    put_pixel(canvas, x, y, gfx_blend(gfx_get_pixel(canvas, x, y), color, alpha));
}

void gfx_clear(gfx_canvas_t *canvas, uint16_t color)
{
    gfx_fill_rect(canvas, 0, 0, canvas->width, canvas->height, color);
}

void gfx_fill_rect(gfx_canvas_t *canvas,
                   int x,
                   int y,
                   int width,
                   int height,
                   uint16_t color)
{
    int x0 = x;
    int y0 = y;
    int x1 = x + width - 1;
    int y1 = y + height - 1;
    if (width <= 0 || height <= 0 || !clip_box(canvas, &x0, &y0, &x1, &y1)) {
        return;
    }
    for (int row = y0; row <= y1; row++) {
        for (int column = x0; column <= x1; column++) {
            put_pixel(canvas, column, row, color);
        }
    }
}

void gfx_fill_round_rect(gfx_canvas_t *canvas,
                         int x,
                         int y,
                         int width,
                         int height,
                         int radius,
                         uint16_t color)
{
    if (width <= 0 || height <= 0) {
        return;
    }
    if (radius * 2 > width) radius = width / 2;
    if (radius * 2 > height) radius = height / 2;
    int x0 = x;
    int y0 = y;
    int x1 = x + width - 1;
    int y1 = y + height - 1;
    if (!clip_box(canvas, &x0, &y0, &x1, &y1)) {
        return;
    }
    /* Corner centers sit on pixel edges so the straight sides stay crisp. */
    const float left = (float)(x + radius);
    const float right = (float)(x + width - radius);
    const float top = (float)(y + radius);
    const float bottom = (float)(y + height - radius);
    for (int row = y0; row <= y1; row++) {
        const float py = (float)row + 0.5f;
        for (int column = x0; column <= x1; column++) {
            const float px = (float)column + 0.5f;
            const float dx = px < left ? left - px : (px > right ? px - right : 0.0f);
            const float dy = py < top ? top - py : (py > bottom ? py - bottom : 0.0f);
            if (dx == 0.0f || dy == 0.0f) {
                put_pixel(canvas, column, row, color);
                continue;
            }
            const float coverage = (float)radius + 0.5f - sqrtf(dx * dx + dy * dy);
            gfx_blend_pixel(canvas, column, row, color, coverage_alpha(coverage, 255));
        }
    }
}

static float segment_distance(float px,
                              float py,
                              float x0,
                              float y0,
                              float x1,
                              float y1)
{
    const float dx = x1 - x0;
    const float dy = y1 - y0;
    const float length_squared = dx * dx + dy * dy;
    float t = 0.0f;
    if (length_squared > 0.0f) {
        t = clampf(((px - x0) * dx + (py - y0) * dy) / length_squared, 0.0f, 1.0f);
    }
    const float ex = px - (x0 + t * dx);
    const float ey = py - (y0 + t * dy);
    return sqrtf(ex * ex + ey * ey);
}

void gfx_line(gfx_canvas_t *canvas,
              float x0,
              float y0,
              float x1,
              float y1,
              float width,
              uint16_t color,
              uint8_t alpha)
{
    const float half = width * 0.5f;
    const float pad = half + 1.0f;
    int bx0 = floor_int(fminf(x0, x1) - pad);
    int by0 = floor_int(fminf(y0, y1) - pad);
    int bx1 = ceil_int(fmaxf(x0, x1) + pad);
    int by1 = ceil_int(fmaxf(y0, y1) + pad);
    if (!clip_box(canvas, &bx0, &by0, &bx1, &by1)) {
        return;
    }
    for (int row = by0; row <= by1; row++) {
        for (int column = bx0; column <= bx1; column++) {
            const float distance =
                segment_distance((float)column, (float)row, x0, y0, x1, y1);
            const float coverage = half + 0.5f - distance;
            if (coverage > 0.0f) {
                gfx_blend_pixel(canvas, column, row, color,
                                coverage_alpha(coverage, alpha));
            }
        }
    }
}

void gfx_dashed_line(gfx_canvas_t *canvas,
                     float x0,
                     float y0,
                     float x1,
                     float y1,
                     float width,
                     float dash,
                     float gap,
                     uint16_t color,
                     uint8_t alpha)
{
    const float dx = x1 - x0;
    const float dy = y1 - y0;
    const float length = sqrtf(dx * dx + dy * dy);
    if (length <= 0.0f || dash <= 0.0f) {
        return;
    }
    const float ux = dx / length;
    const float uy = dy / length;
    for (float start = 0.0f; start < length; start += dash + gap) {
        const float end = fminf(start + dash, length);
        gfx_line(canvas,
                 x0 + ux * start, y0 + uy * start,
                 x0 + ux * end, y0 + uy * end,
                 width, color, alpha);
    }
}

static float wrap_degrees(float degrees)
{
    degrees = fmodf(degrees, 360.0f);
    return degrees < 0.0f ? degrees + 360.0f : degrees;
}

static void ring_span(gfx_canvas_t *canvas,
                      float cx,
                      float cy,
                      float radius,
                      float width,
                      bool limit_angle,
                      float start_deg,
                      float sweep_deg,
                      uint16_t color,
                      uint8_t alpha)
{
    const float half = width * 0.5f;
    const float outer = radius + half + 1.0f;
    int x0 = floor_int(cx - outer);
    int y0 = floor_int(cy - outer);
    int x1 = ceil_int(cx + outer);
    int y1 = ceil_int(cy + outer);
    if (!clip_box(canvas, &x0, &y0, &x1, &y1)) {
        return;
    }
    const float inner_skip = fmaxf(0.0f, radius - half - 1.0f);
    for (int row = y0; row <= y1; row++) {
        const float dy = (float)row - cy;
        for (int column = x0; column <= x1; column++) {
            const float dx = (float)column - cx;
            const float distance = sqrtf(dx * dx + dy * dy);
            if (distance < inner_skip || distance > outer) {
                continue;
            }
            const float coverage = half + 0.5f - fabsf(distance - radius);
            if (coverage <= 0.0f) {
                continue;
            }
            if (limit_angle) {
                /* Screen y grows downward; flip so positive angles turn counter-clockwise. */
                const float angle = wrap_degrees(atan2f(-dy, dx) * 57.29578f);
                if (wrap_degrees(angle - start_deg) > sweep_deg) {
                    continue;
                }
            }
            gfx_blend_pixel(canvas, column, row, color,
                            coverage_alpha(coverage, alpha));
        }
    }
}

void gfx_ring(gfx_canvas_t *canvas,
              float cx,
              float cy,
              float radius,
              float width,
              uint16_t color,
              uint8_t alpha)
{
    ring_span(canvas, cx, cy, radius, width, false, 0.0f, 360.0f, color, alpha);
}

void gfx_arc(gfx_canvas_t *canvas,
             float cx,
             float cy,
             float radius,
             float width,
             float start_deg,
             float end_deg,
             uint16_t color,
             uint8_t alpha)
{
    float sweep = end_deg - start_deg;
    if (sweep < 0.0f) {
        start_deg = end_deg;
        sweep = -sweep;
    }
    if (sweep >= 360.0f) {
        gfx_ring(canvas, cx, cy, radius, width, color, alpha);
        return;
    }
    ring_span(canvas, cx, cy, radius, width, true,
              wrap_degrees(start_deg), sweep, color, alpha);
}

void gfx_fill_circle(gfx_canvas_t *canvas,
                     float cx,
                     float cy,
                     float radius,
                     uint16_t color,
                     uint8_t alpha)
{
    const float outer = radius + 1.0f;
    int x0 = floor_int(cx - outer);
    int y0 = floor_int(cy - outer);
    int x1 = ceil_int(cx + outer);
    int y1 = ceil_int(cy + outer);
    if (!clip_box(canvas, &x0, &y0, &x1, &y1)) {
        return;
    }
    for (int row = y0; row <= y1; row++) {
        const float dy = (float)row - cy;
        for (int column = x0; column <= x1; column++) {
            const float dx = (float)column - cx;
            const float coverage = radius + 0.5f - sqrtf(dx * dx + dy * dy);
            if (coverage > 0.0f) {
                gfx_blend_pixel(canvas, column, row, color,
                                coverage_alpha(coverage, alpha));
            }
        }
    }
}

int gfx_text_width(ui_font_id_t font, const char *text)
{
    return ui_font_text_width(font, text);
}

int gfx_text(gfx_canvas_t *canvas,
             int x,
             int baseline,
             ui_font_id_t font,
             uint16_t color,
             const char *text)
{
    if (!text || (unsigned)font >= UI_FONT_COUNT) {
        return 0;
    }
    const uint8_t *bitmap = ui_fonts[font].bitmap;
    const int origin = x;
    const char *cursor = text;
    while (*cursor) {
        const ui_glyph_t *glyph =
            ui_font_glyph_or_fallback(font, ui_font_next_codepoint(&cursor));
        if (!glyph) {
            continue;
        }
        const uint8_t *pixels = bitmap + glyph->offset;
        const int left = x + glyph->x_offset;
        const int top = baseline + glyph->y_offset;
        for (int row = 0; row < glyph->height; row++) {
            for (int column = 0; column < glyph->width; column++) {
                const size_t index = (size_t)row * glyph->width + column;
                const uint8_t packed = pixels[index / 2];
                const uint8_t level = (index & 1) ? (packed & 0x0F) : (packed >> 4);
                if (level) {
                    gfx_blend_pixel(canvas, left + column, top + row, color,
                                    (uint8_t)(level * 17));
                }
            }
        }
        x += glyph->advance;
    }
    return x - origin;
}
