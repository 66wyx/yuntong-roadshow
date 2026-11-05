/*
 * Host preview: renders rid_ui_draw() scenes to binary PPM files.
 *
 *   ui_preview <output-dir>
 *
 * The same rid_ui.c / rid_gfx.c / ui_font*.c sources run on the ESP32-P4,
 * so these images are the pixels the panel receives (RGB565 expanded).
 */

#include <math.h>
#include <stdio.h>
#include <string.h>

#include "rid_ui.h"

#define WIDTH 240
#define HEIGHT 320
#define ANCHOR_LAT 22.6
#define ANCHOR_LON 114.3

static uint8_t s_pixels[WIDTH * HEIGHT * 2];

static rid_target_snapshot_t make_target(const char *id,
                                         uint8_t mac_tail,
                                         uint8_t vendor_type,
                                         double east_m,
                                         double north_m,
                                         double up_m,
                                         double track_deg,
                                         double speed_mps,
                                         uint64_t position_age_ms,
                                         uint64_t now_ms)
{
    rid_target_snapshot_t target;
    memset(&target, 0, sizeof(target));
    rid_observation_t *o = &target.observation;
    o->decoded = true;
    o->position_valid = true;
    o->identity_valid = id != NULL;
    if (id) {
        snprintf(o->uas_id, sizeof(o->uas_id), "%s", id);
    }
    snprintf(o->protocol, sizeof(o->protocol),
             vendor_type == RID_VENDOR_TYPE_GB ? "gb46750_2025" : "astm_f3411");
    o->vendor_type = vendor_type;
    o->source_mac[5] = mac_tail;
    o->channel = 6;
    o->rssi = -58;
    o->latitude = ANCHOR_LAT + north_m / 110540.0;
    o->longitude = ANCHOR_LON + east_m / (111320.0 * cos(ANCHOR_LAT * M_PI / 180.0));
    o->altitude_geo_m = up_m;
    o->altitude_geo_valid = true;
    o->height_m = up_m;
    o->height_valid = true;
    o->direction_deg = track_deg;
    o->direction_valid = true;
    o->speed_horizontal_mps = speed_mps;
    o->speed_valid = true;
    target.rssi = o->rssi;
    target.first_seen_ms = now_ms - 30000;
    target.last_position_ms = now_ms - position_age_ms;
    target.last_seen_ms = target.last_position_ms;
    target.message_count = 120;
    return target;
}

static int write_ppm(const char *directory, const char *name)
{
    char path[512];
    snprintf(path, sizeof(path), "%s/%s.ppm", directory, name);
    FILE *file = fopen(path, "wb");
    if (!file) {
        perror(path);
        return 1;
    }
    fprintf(file, "P6\n%d %d\n255\n", WIDTH, HEIGHT);
    for (size_t i = 0; i < WIDTH * HEIGHT; i++) {
        const uint16_t c = (uint16_t)((s_pixels[i * 2] << 8) | s_pixels[i * 2 + 1]);
        const uint8_t rgb[3] = {
            (uint8_t)(((c >> 11) & 0x1F) * 255 / 31),
            (uint8_t)(((c >> 5) & 0x3F) * 255 / 63),
            (uint8_t)((c & 0x1F) * 255 / 31),
        };
        fwrite(rgb, 1, 3, file);
    }
    fclose(file);
    printf("%s\n", path);
    return 0;
}

static int render(const char *directory,
                  const char *name,
                  rid_ui_page_t page,
                  const rid_target_snapshot_t *targets,
                  size_t count,
                  uint32_t mgmt,
                  uint32_t rid)
{
    gfx_canvas_t canvas = {s_pixels, WIDTH, HEIGHT};
    const rid_ui_frame_t frame = {
        .page = page,
        .now_ms = 600000,
        .stats = {.channel = 6, .mgmt_frames = mgmt, .rid_frames = rid,
                  .decoded_frames = rid},
        .targets = targets,
        .target_count = count,
    };
    rid_ui_draw(&canvas, &frame);
    return write_ppm(directory, name);
}

int main(int argc, char **argv)
{
    if (argc != 2) {
        fprintf(stderr, "usage: %s <output-dir>\n", argv[0]);
        return 2;
    }
    const char *out = argv[1];
    const uint64_t now = 600000;

    rid_target_snapshot_t scene[3] = {
        make_target("1581F5FKD229400DA1", 1, RID_VENDOR_TYPE_GB,
                    86.0, 142.0, 62.0, 248.0, 7.4, 400, now),
        make_target("LAB-TEST-001", 2, RID_VENDOR_TYPE_ASTM,
                    -150.0, 40.0, 95.0, 90.0, 4.0, 900, now),
        make_target("GB-DEMO-002", 3, RID_VENDOR_TYPE_GB,
                    60.0, -120.0, 40.0, 0.0, 0.0, 7000, now),
    };
    rid_target_snapshot_t identity_only = scene[1];
    identity_only.observation.position_valid = false;
    identity_only.last_position_ms = 0;

    int status = 0;
    status |= render(out, "radar-empty", RID_UI_RADAR, NULL, 0, 1813398, 0);
    status |= render(out, "radar-live", RID_UI_RADAR, scene, 3, 1813398, 412);
    status |= render(out, "height-live", RID_UI_HEIGHT, scene, 3, 1813398, 412);
    status |= render(out, "radar-stale", RID_UI_RADAR, &scene[2], 1, 1813398, 412);
    status |= render(out, "radar-identity-only", RID_UI_RADAR, &identity_only, 1,
                     1813398, 9);
    return status;
}
