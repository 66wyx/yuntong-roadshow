#include "ui_font.h"

uint32_t ui_font_next_codepoint(const char **cursor)
{
    const unsigned char *text = (const unsigned char *)*cursor;
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

const ui_glyph_t *ui_font_glyph(ui_font_id_t font, uint32_t codepoint)
{
    if ((unsigned)font >= UI_FONT_COUNT) {
        return NULL;
    }
    const ui_glyph_t *glyphs = ui_fonts[font].glyphs;
    size_t low = 0;
    size_t high = ui_fonts[font].glyph_count;
    while (low < high) {
        size_t middle = low + (high - low) / 2;
        if (glyphs[middle].codepoint < codepoint) {
            low = middle + 1;
        } else {
            high = middle;
        }
    }
    if (low < ui_fonts[font].glyph_count &&
        glyphs[low].codepoint == codepoint) {
        return &glyphs[low];
    }
    return NULL;
}

const ui_glyph_t *ui_font_glyph_or_fallback(ui_font_id_t font,
                                            uint32_t codepoint)
{
    const ui_glyph_t *glyph = ui_font_glyph(font, codepoint);
    return glyph ? glyph : ui_font_glyph(font, '?');
}

int ui_font_text_width(ui_font_id_t font, const char *text)
{
    if (!text) {
        return 0;
    }
    int width = 0;
    const char *cursor = text;
    while (*cursor) {
        const ui_glyph_t *glyph =
            ui_font_glyph_or_fallback(font, ui_font_next_codepoint(&cursor));
        if (glyph) {
            width += glyph->advance;
        }
    }
    return width;
}
