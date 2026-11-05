#ifndef RID_UI_H
#define RID_UI_H

#include <stddef.h>
#include <stdint.h>

#include "rid_gfx.h"
#include "rid_runtime.h"

typedef enum {
    RID_UI_RADAR = 0,
    RID_UI_HEIGHT = 1,
} rid_ui_page_t;

typedef struct {
    uint8_t channel;
    uint32_t mgmt_frames;
    uint32_t rid_frames;
    uint32_t decoded_frames;
} rid_ui_stats_t;

typedef struct {
    rid_ui_page_t page;
    uint64_t now_ms;
    rid_ui_stats_t stats;
    const rid_target_snapshot_t *targets;
    size_t target_count;
} rid_ui_frame_t;

/* Pure renderer: draws one complete frame; no hardware or RTOS access. */
void rid_ui_draw(gfx_canvas_t *canvas, const rid_ui_frame_t *frame);

#endif
