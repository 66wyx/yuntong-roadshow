#ifndef RID_UI_H
#define RID_UI_H

#include <stdbool.h>
#include <stdint.h>

typedef enum {
    RID_UI_RADAR = 0,
    RID_UI_HEIGHT = 1,
} rid_ui_page_t;

bool rid_ui_init(void);
void rid_ui_render(rid_ui_page_t page, uint64_t now_ms);

#endif
