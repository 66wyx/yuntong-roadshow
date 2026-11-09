#ifndef RID_RUNTIME_H
#define RID_RUNTIME_H

#include <stddef.h>
#include <stdint.h>

#include "rid_decoder.h"

#define RID_RUNTIME_MAX_TARGETS 8
#define RID_POSITION_STALE_MS 3000
#define RID_TARGET_EXPIRE_MS 10000

typedef struct {
    rid_observation_t observation;
    uint64_t first_seen_ms;
    uint64_t last_seen_ms;
    uint64_t last_position_ms;
    uint32_t message_count;
    int rssi;
} rid_target_snapshot_t;

void rid_runtime_apply(const rid_observation_t *observation, uint64_t now_ms);
size_t rid_runtime_snapshot(uint64_t now_ms,
                            rid_target_snapshot_t *targets,
                            size_t capacity);

#endif
