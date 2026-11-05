#ifndef RID_GEO_H
#define RID_GEO_H

#include <stdbool.h>

#include "rid_decoder.h"

typedef struct {
    double latitude;
    double longitude;
    double altitude_m;  /* WGS84 geodetic, same datum as RID geodetic altitude */
} rid_geo_anchor_t;

/* Receiver east/north/up offsets of a target, in metres. */
typedef struct {
    double east_m;
    double north_m;
    double up_m;        /* target geodetic altitude minus receiver altitude */
    bool up_valid;
} rid_enu_t;

/*
 * Bench receiver position. EVT0 has no GNSS, so this must match the
 * --origin-* arguments given to tools/virtual-rid-tx/virtual_rid_tx.py.
 */
extern const rid_geo_anchor_t rid_receiver_anchor;

/* Same flat-earth projection as virtual_rid_tx.local_to_wgs84, inverted. */
rid_enu_t rid_geo_to_enu(const rid_geo_anchor_t *anchor,
                         const rid_observation_t *observation);
double rid_geo_horizontal_m(const rid_enu_t *enu);
/* True-north bearing, clockwise, 0 <= bearing < 360. */
double rid_geo_bearing_deg(const rid_enu_t *enu);

#endif
