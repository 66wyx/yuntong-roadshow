#include <string.h>

#include "freertos/FreeRTOS.h"

#include "rid_runtime.h"

typedef struct {
    rid_observation_t observation;
    uint64_t first_seen_ms;
    uint64_t last_seen_ms;
    uint64_t last_position_ms;
    uint32_t message_count;
    int rssi;
    bool used;
} rid_target_record_t;

static rid_target_record_t s_targets[RID_RUNTIME_MAX_TARGETS];
static portMUX_TYPE s_targets_lock = portMUX_INITIALIZER_UNLOCKED;

static bool same_mac(const uint8_t *left, const uint8_t *right)
{
    return memcmp(left, right, 6) == 0;
}

static rid_target_record_t *find_or_allocate(const uint8_t *mac,
                                             uint64_t now_ms)
{
    rid_target_record_t *oldest = NULL;
    for (size_t i = 0; i < RID_RUNTIME_MAX_TARGETS; i++) {
        rid_target_record_t *record = &s_targets[i];
        if (record->used && same_mac(record->observation.source_mac, mac)) {
            return record;
        }
        if (!record->used) {
            record->used = true;
            record->first_seen_ms = now_ms;
            return record;
        }
        if (!oldest || record->last_seen_ms < oldest->last_seen_ms) {
            oldest = record;
        }
    }
    memset(oldest, 0, sizeof(*oldest));
    oldest->used = true;
    oldest->first_seen_ms = now_ms;
    return oldest;
}

void rid_runtime_apply(const rid_observation_t *observation, uint64_t now_ms)
{
    if (!observation || !observation->decoded) {
        return;
    }

    portENTER_CRITICAL(&s_targets_lock);
    rid_target_record_t *record =
        find_or_allocate(observation->source_mac, now_ms);
    record->last_seen_ms = now_ms;
    record->message_count++;
    record->rssi = observation->rssi;

    if (observation->identity_valid) {
        memcpy(record->observation.uas_id,
               observation->uas_id,
               sizeof(record->observation.uas_id));
        memcpy(record->observation.registration_id,
               observation->registration_id,
               sizeof(record->observation.registration_id));
        record->observation.identity_valid = true;
    }
    if (observation->protocol[0]) {
        memcpy(record->observation.protocol,
               observation->protocol,
               sizeof(record->observation.protocol));
    }
    memcpy(record->observation.source_mac,
           observation->source_mac,
           sizeof(record->observation.source_mac));
    if (observation->operator_id[0]) {
        memcpy(record->observation.operator_id,
               observation->operator_id,
               sizeof(record->observation.operator_id));
    }
    record->observation.vendor_type = observation->vendor_type;
    record->observation.rssi = observation->rssi;
    record->observation.channel = observation->channel;

    if (observation->position_valid) {
        /* Kinematics travel with the position report they belong to. */
        record->observation.latitude = observation->latitude;
        record->observation.longitude = observation->longitude;
        record->observation.altitude_geo_m = observation->altitude_geo_m;
        record->observation.altitude_geo_valid =
            observation->altitude_geo_valid;
        record->observation.height_m = observation->height_m;
        record->observation.height_valid = observation->height_valid;
        record->observation.direction_deg = observation->direction_deg;
        record->observation.direction_valid = observation->direction_valid;
        record->observation.speed_horizontal_mps =
            observation->speed_horizontal_mps;
        record->observation.speed_valid = observation->speed_valid;
        record->observation.speed_vertical_mps =
            observation->speed_vertical_mps;
        record->observation.position_valid = true;
        record->last_position_ms = now_ms;
    }
    record->observation.decoded = true;
    portEXIT_CRITICAL(&s_targets_lock);
}

size_t rid_runtime_snapshot(uint64_t now_ms,
                            rid_target_snapshot_t *targets,
                            size_t capacity)
{
    if (!targets || !capacity) {
        return 0;
    }

    size_t count = 0;
    portENTER_CRITICAL(&s_targets_lock);
    for (size_t i = 0; i < RID_RUNTIME_MAX_TARGETS; i++) {
        rid_target_record_t *record = &s_targets[i];
        if (!record->used ||
            now_ms - record->last_seen_ms > RID_TARGET_EXPIRE_MS) {
            continue;
        }
        if (count < capacity) {
            rid_target_snapshot_t *snapshot = &targets[count++];
            snapshot->observation = record->observation;
            snapshot->first_seen_ms = record->first_seen_ms;
            snapshot->last_seen_ms = record->last_seen_ms;
            snapshot->last_position_ms = record->last_position_ms;
            snapshot->message_count = record->message_count;
            snapshot->rssi = record->rssi;
        }
    }
    portEXIT_CRITICAL(&s_targets_lock);

    for (size_t i = 1; i < count; i++) {
        rid_target_snapshot_t item = targets[i];
        size_t position = i;
        while (position > 0 &&
               targets[position - 1].last_seen_ms < item.last_seen_ms) {
            targets[position] = targets[position - 1];
            position--;
        }
        targets[position] = item;
    }
    return count;
}
