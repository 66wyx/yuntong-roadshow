"""Host-side validation for the C RID decoder against repository fixtures."""

from __future__ import annotations

import ctypes
import math
from pathlib import Path
import sys


HERE = Path(__file__).resolve()
FIXTURE_DIR = HERE.parents[3] / "tools" / "virtual-rid-tx"
if not (FIXTURE_DIR / "rid_fixtures.py").is_file():
    raise SystemExit(f"Unable to locate rid_fixtures.py in {FIXTURE_DIR}")
sys.path.insert(0, str(FIXTURE_DIR))

import rid_fixtures  # noqa: E402


class Observation(ctypes.Structure):
    """Mirror of rid_observation_t in main/rid_decoder.h; keep in sync."""

    _fields_ = [
        ("decoded", ctypes.c_bool),
        ("position_valid", ctypes.c_bool),
        ("identity_valid", ctypes.c_bool),
        ("altitude_geo_valid", ctypes.c_bool),
        ("height_valid", ctypes.c_bool),
        ("direction_valid", ctypes.c_bool),
        ("speed_valid", ctypes.c_bool),
        ("protocol", ctypes.c_char * 16),
        ("uas_id", ctypes.c_char * 21),
        ("registration_id", ctypes.c_char * 9),
        ("operator_id", ctypes.c_char * 21),
        ("source_mac", ctypes.c_uint8 * 6),
        ("vendor_type", ctypes.c_uint8),
        ("rssi", ctypes.c_int),
        ("channel", ctypes.c_uint8),
        ("latitude", ctypes.c_double),
        ("longitude", ctypes.c_double),
        ("altitude_geo_m", ctypes.c_double),
        ("height_m", ctypes.c_double),
        ("direction_deg", ctypes.c_double),
        ("speed_horizontal_mps", ctypes.c_double),
        ("speed_vertical_mps", ctypes.c_double),
    ]


def decode(library, frame):
    observation = Observation()
    buffer = ctypes.create_string_buffer(frame)
    ok = library.rid_decode_frame(
        buffer, len(frame), -51, 6, ctypes.byref(observation)
    )
    assert ok
    return observation


def close(actual, expected, tolerance=1e-5):
    assert math.isclose(actual, expected, abs_tol=tolerance), (actual, expected)


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: test_rid_decoder.py /path/to/librid_decoder.so")
    library = ctypes.CDLL(sys.argv[1])
    library.rid_decode_frame.argtypes = [
        ctypes.c_void_p,
        ctypes.c_size_t,
        ctypes.c_int,
        ctypes.c_uint8,
        ctypes.POINTER(Observation),
    ]
    library.rid_decode_frame.restype = ctypes.c_bool

    astm = decode(library, rid_fixtures.astm_frame())
    assert astm.protocol == b"astm_f3411"
    assert astm.uas_id == b"LAB-TEST-001"
    close(astm.latitude, 22.6)
    close(astm.longitude, 114.3)
    close(astm.altitude_geo_m, 125.0)
    close(astm.height_m, 62.0)

    assert astm.operator_id == b"DEMO-OPERATOR"
    assert astm.altitude_geo_valid and astm.height_valid

    for track in (0, 90, 179, 180, 270, 359):
        item = decode(library, rid_fixtures.astm_frame(track_deg=track, speed_mps=12.0))
        assert item.direction_valid
        close(item.direction_deg, track)
        close(item.speed_horizontal_mps, 12.0)

    gb = decode(library, rid_fixtures.gb46750_frame())
    assert gb.protocol == b"gb46750_2025"
    assert gb.uas_id == b"GB-DEMO-002"
    assert gb.registration_id == b"UAS00002"
    close(gb.latitude, 22.5987)
    close(gb.longitude, 114.3012)
    close(gb.height_m, 75.0)
    close(gb.altitude_geo_m, 155.0)
    close(gb.direction_deg, 27.5)
    close(gb.speed_horizontal_mps, 8.8)
    print("C RID decoder fixtures passed")


if __name__ == "__main__":
    main()
