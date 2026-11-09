#include <math.h>

#include "rid_geo.h"

#define METRES_PER_DEGREE_LATITUDE 110540.0
#define METRES_PER_DEGREE_LONGITUDE_AT_EQUATOR 111320.0
#define DEGREES_TO_RADIANS 0.017453292519943295

const rid_geo_anchor_t rid_receiver_anchor = {
    .latitude = 22.6000000,
    .longitude = 114.3000000,
    .altitude_m = 0.0,
};

rid_enu_t rid_geo_to_enu(const rid_geo_anchor_t *anchor,
                         const rid_observation_t *observation)
{
    rid_enu_t enu = {0};
    enu.east_m = (observation->longitude - anchor->longitude) *
                 METRES_PER_DEGREE_LONGITUDE_AT_EQUATOR *
                 cos(anchor->latitude * DEGREES_TO_RADIANS);
    enu.north_m = (observation->latitude - anchor->latitude) *
                  METRES_PER_DEGREE_LATITUDE;
    enu.up_valid = observation->altitude_geo_valid;
    enu.up_m = enu.up_valid ? observation->altitude_geo_m - anchor->altitude_m
                            : 0.0;
    return enu;
}

double rid_geo_horizontal_m(const rid_enu_t *enu)
{
    return sqrt(enu->east_m * enu->east_m + enu->north_m * enu->north_m);
}

double rid_geo_bearing_deg(const rid_enu_t *enu)
{
    double bearing = atan2(enu->east_m, enu->north_m) / DEGREES_TO_RADIANS;
    if (bearing < 0.0) {
        bearing += 360.0;
    }
    return bearing >= 360.0 ? 0.0 : bearing;
}
