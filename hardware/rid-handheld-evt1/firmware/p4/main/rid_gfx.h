#ifndef RID_GFX_H
#define RID_GFX_H

#include <stdint.h>

#include "ui_font.h"

/* Compile-time RGB565 color. */
#define GFX_RGB(r, g, b)                                   \
    ((uint16_t)((((unsigned)(r) & 0xF8u) << 8) |           \
                (((unsigned)(g) & 0xFCu) << 3) |           \
                ((unsigned)(b) >> 3)))

/*
 * Framebuffer in panel byte order: big-endian RGB565, row-major.
 * Shapes use pixel centers at integer coordinates; rectangles use edges.
 * Every primitive clips to the canvas.
 */
typedef struct {
    uint8_t *pixels;
    int width;
    int height;
} gfx_canvas_t;

void gfx_clear(gfx_canvas_t *canvas, uint16_t color);
uint16_t gfx_get_pixel(const gfx_canvas_t *canvas, int x, int y);
void gfx_blend_pixel(gfx_canvas_t *canvas,
                     int x,
                     int y,
                     uint16_t color,
                     uint8_t alpha);
uint16_t gfx_blend(uint16_t background, uint16_t foreground, uint8_t alpha);

void gfx_fill_rect(gfx_canvas_t *canvas,
                   int x,
                   int y,
                   int width,
                   int height,
                   uint16_t color);
void gfx_fill_round_rect(gfx_canvas_t *canvas,
                         int x,
                         int y,
                         int width,
                         int height,
                         int radius,
                         uint16_t color);

void gfx_line(gfx_canvas_t *canvas,
              float x0,
              float y0,
              float x1,
              float y1,
              float width,
              uint16_t color,
              uint8_t alpha);
void gfx_dashed_line(gfx_canvas_t *canvas,
                     float x0,
                     float y0,
                     float x1,
                     float y1,
                     float width,
                     float dash,
                     float gap,
                     uint16_t color,
                     uint8_t alpha);

void gfx_ring(gfx_canvas_t *canvas,
              float cx,
              float cy,
              float radius,
              float width,
              uint16_t color,
              uint8_t alpha);
/* Angles in degrees: 0 points right, positive turns counter-clockwise on screen. */
void gfx_arc(gfx_canvas_t *canvas,
             float cx,
             float cy,
             float radius,
             float width,
             float start_deg,
             float end_deg,
             uint16_t color,
             uint8_t alpha);
void gfx_fill_circle(gfx_canvas_t *canvas,
                     float cx,
                     float cy,
                     float radius,
                     uint16_t color,
                     uint8_t alpha);

/* Draws UTF-8 text with its baseline at y; returns the advance width. */
int gfx_text(gfx_canvas_t *canvas,
             int x,
             int baseline,
             ui_font_id_t font,
             uint16_t color,
             const char *text);
int gfx_text_width(ui_font_id_t font, const char *text);

#endif
