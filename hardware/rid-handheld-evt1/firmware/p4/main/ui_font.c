#include <stddef.h>

#include "ui_font.h"
#include "ui_font_data.h"

static uint32_t decode_utf8(const unsigned char **cursor)
{
    const unsigned char *text = *cursor;
    if (text[0] < 0x80) {
        (*cursor)++;
        return text[0];
    }
    if ((text[0] & 0xE0) == 0xC0 && (text[1] & 0xC0) == 0x80) {
        *cursor += 2;
        return ((uint32_t)(text[0] & 0x1F) << 6) |
               (uint32_t)(text[1] & 0x3F);
    }
    if ((text[0] & 0xF0) == 0xE0 &&
        (text[1] & 0xC0) == 0x80 &&
        (text[2] & 0xC0) == 0x80) {
        *cursor += 3;
        return ((uint32_t)(text[0] & 0x0F) << 12) |
               ((uint32_t)(text[1] & 0x3F) << 6) |
               (uint32_t)(text[2] & 0x3F);
    }
    (*cursor)++;
    return '?';
}

static const ui_glyph_t *find_glyph(const ui_glyph_t *glyphs,
                                    size_t count,
                                    uint32_t codepoint)
{
    size_t low = 0;
    size_t high = count;
    while (low < high) {
        size_t middle = low + (high - low) / 2;
        if (glyphs[middle].codepoint < codepoint) {
            low = middle + 1;
        } else {
            high = middle;
        }
    }
    if (low < count && glyphs[low].codepoint == codepoint) {
        return &glyphs[low];
    }
    return NULL;
}

static const ui_glyph_t *lookup(uint32_t codepoint, int large)
{
    const ui_glyph_t *glyph =
        large ? find_glyph(ui_big_glyphs, UI_BIG_GLYPH_COUNT, codepoint)
              : find_glyph(ui_small_glyphs, UI_SMALL_GLYPH_COUNT, codepoint);
    if (!glyph) {
        glyph = large ? find_glyph(ui_big_glyphs, UI_BIG_GLYPH_COUNT, '?')
                      : find_glyph(ui_small_glyphs, UI_SMALL_GLYPH_COUNT, '?');
    }
    return glyph;
}

int ui_font_width(const char *text, int large)
{
    if (!text) {
        return 0;
    }
    int width = 0;
    const unsigned char *cursor = (const unsigned char *)text;
    while (*cursor) {
        const ui_glyph_t *glyph = lookup(decode_utf8(&cursor), large);
        if (glyph) {
            width += glyph->width + 1;
        }
    }
    return width;
}

int ui_font_draw(void (*plot)(int x, int y, void *context),
                 void *context,
                 const char *text,
                 int x,
                 int y,
                 uint16_t color,
                 int large)
{
    if (!plot || !text) {
        return x;
    }
    int origin_x = x;
    const unsigned char *cursor = (const unsigned char *)text;
    while (*cursor) {
        const ui_glyph_t *glyph = lookup(decode_utf8(&cursor), large);
        if (!glyph) {
            continue;
        }
        for (uint8_t row = 0; row < glyph->height; row++) {
            for (uint8_t column = 0; column < glyph->width; column++) {
                if (glyph->rows[row] & (1u << column)) {
                    plot(x + column, y + row, context);
                }
            }
        }
        x += glyph->width + 1;
    }
    return x - origin_x;
}
