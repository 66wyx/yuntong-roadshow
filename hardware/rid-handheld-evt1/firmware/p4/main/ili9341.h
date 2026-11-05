#ifndef ILI9341_H
#define ILI9341_H

#include <stdbool.h>

#include "rid_gfx.h"

#define ILI9341_WIDTH 240
#define ILI9341_HEIGHT 320

bool ili9341_init(void);
/* Full-screen framebuffer; draw with rid_gfx, then call ili9341_flush(). */
gfx_canvas_t *ili9341_canvas(void);
void ili9341_flush(void);

#endif
