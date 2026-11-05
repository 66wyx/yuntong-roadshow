#ifndef RID_DECODER_H
#define RID_DECODER_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define RID_VENDOR_TYPE_ASTM 0x0D
#define RID_VENDOR_TYPE_GB   0xF0

typedef struct {
    bool decoded;
    bool position_valid;
    bool identity_valid;
    bool altitude_geo_valid;
    bool height_valid;
    bool direction_valid;
    bool speed_valid;
    char protocol[16];
    char uas_id[21];
    char registration_id[9];
    char operator_id[21];
    uint8_t source_mac[6];
    uint8_t vendor_type;
    int rssi;
    uint8_t channel;
    double latitude;
    double longitude;
    double altitude_geo_m;     /* WGS84 geodetic altitude */
    double height_m;           /* above take-off or ground, not receiver */
    double direction_deg;      /* track over ground, true north, clockwise */
    double speed_horizontal_mps;
    double speed_vertical_mps;
} rid_observation_t;

bool rid_decode_frame(const uint8_t *frame,
                      size_t frame_len,
                      int rssi,
                      uint8_t channel,
                      rid_observation_t *out);

#endif
