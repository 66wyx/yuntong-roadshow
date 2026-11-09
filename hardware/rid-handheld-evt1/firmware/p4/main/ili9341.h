#ifndef ILI9341_H
#define ILI9341_H

#include <stdbool.h>
#include <stdint.h>

#define ILI9341_WIDTH 240
#define ILI9341_HEIGHT 320

uint16_t ili9341_rgb565(uint8_t red, uint8_t green, uint8_t blue);
bool ili9341_init(void);
void ili9341_flush(void);

void ili9341_clear(uint16_t color);
void ili9341_pixel(int x, int y, uint16_t color);
void ili9341_fill_rect(int x, int y, int width, int height, uint16_t color);
void ili9341_line(int x0, int y0, int x1, int y1, uint16_t color);
void ili9341_ellipse(int cx, int cy, int rx, int ry, uint16_t color);
void ili9341_fill_circle(int cx, int cy, int radius, uint16_t color);

#endif
