#ifndef UI_FONT_H
#define UI_FONT_H

#include <stdint.h>

typedef struct {
    uint32_t codepoint;
    uint8_t width;
    uint8_t height;
    const uint32_t *rows;
} ui_glyph_t;

int ui_font_width(const char *text, int large);
int ui_font_draw(void (*plot)(int x, int y, void *context),
                 void *context,
                 const char *text,
                 int x,
                 int y,
                 uint16_t color,
                 int large);

#endif
