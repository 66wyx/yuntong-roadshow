"""Host tests for the RID decoder, packet fixtures and target state."""

import unittest

import rid_decoder
import rid_fixtures
import rid_state
import virtual_rid_tx


class DecoderTests(unittest.TestCase):
    def test_astm_pack_decodes_identity_and_position(self):
        frame = rid_fixtures.astm_frame()
        observations = rid_decoder.decode_wifi_frame(
            frame, rssi=-51, channel=6, now_ms=1000
        )
        self.assertEqual(len(observations), 1)
        item = observations[0]
        self.assertEqual(item["protocol"], "astm_f3411")
        self.assertEqual(item["uas_id"], "LAB-TEST-001")
        self.assertEqual(item["message_types"], [0, 1, 4, 5])
        self.assertEqual(item["latitude"], 22.6)
        self.assertEqual(item["longitude"], 114.3)
        self.assertEqual(item["altitude_geo_m"], 125.0)
        self.assertEqual(item["height_m"], 62.0)
        self.assertEqual(item["operator_id"], "DEMO-OPERATOR")
        self.assertEqual(item["rssi_dbm"], -51)
        self.assertEqual(item["channel"], 6)

    def test_gb46750_decodes_flags_and_fields(self):
        frame = rid_fixtures.gb46750_frame()
        observations = rid_decoder.decode_wifi_frame(
            frame, rssi=-62, channel=149, now_ms=1000
        )
        self.assertEqual(len(observations), 1)
        item = observations[0]
        self.assertEqual(item["protocol"], "gb46750_2025")
        self.assertEqual(item["uas_id"], "GB-DEMO-002")
        self.assertEqual(item["registration_id"], "UAS00002")
        self.assertEqual(item["latitude"], 22.5987)
        self.assertEqual(item["longitude"], 114.3012)
        self.assertEqual(item["height_m"], 75.0)
        self.assertEqual(item["operator_latitude"], 22.5992)
        self.assertEqual(item["operator_longitude"], 114.2995)
        self.assertEqual(item["timestamp_unix_ms"], 1_800_000_000_000)
        self.assertIn("operator_location", item["present_fields"])

    def test_truncated_payloads_are_rejected(self):
        with self.assertRaises(ValueError):
            rid_decoder.decode_astm_payload(b"\x00\xf2\x19\x02")
        with self.assertRaises(ValueError):
            rid_decoder.decode_gb46750_payload(b"\xff\x20\x10\x80")

    def test_non_beacon_frame_is_ignored(self):
        frame = bytearray(rid_fixtures.astm_frame())
        frame[0] = 0x08
        self.assertEqual(rid_decoder.decode_wifi_frame(frame), [])


class StateTests(unittest.TestCase):
    def observation(self, frame, now):
        return rid_decoder.decode_wifi_frame(frame, now_ms=now)[0]

    def test_target_becomes_stale_then_expired(self):
        store = rid_state.TargetStore()
        observation = self.observation(rid_fixtures.astm_frame(), 0)
        target = store.apply(observation, 0)
        self.assertEqual(store.state(target, 0), "active")
        self.assertEqual(store.state(target, 3001), "stale")
        self.assertEqual(store.state(target, 10001), "expired")

    def test_identity_refresh_does_not_refresh_position(self):
        store = rid_state.TargetStore()
        frame = rid_fixtures.astm_frame()
        target = store.apply(self.observation(frame, 1000), 1000)
        identity = {
            "protocol": "astm_f3411",
            "source_mac": "02:00:00:00:00:01",
            "uas_id": "LAB-TEST-001",
        }
        target = store.apply(identity, 5000)
        self.assertEqual(store.state(target, 5000), "stale")
        self.assertEqual(target["last_position_ms"], 1000)

    def test_snapshot_keeps_identity_only_target_out_of_radar(self):
        store = rid_state.TargetStore()
        store.apply(
            {
                "protocol": "astm_f3411",
                "source_mac": "02:00:00:00:00:03",
                "uas_id": "IDENTITY-ONLY",
            },
            1000,
        )
        self.assertEqual(store.active_positions(1000), [])
        self.assertEqual(store.snapshot(1000)[0]["state"], "identity_only")


class MotionTests(unittest.TestCase):
    def test_local_xyz_conversion_is_near_expected_distance(self):
        latitude, longitude, altitude = virtual_rid_tx.local_to_wgs84(
            100.0,
            200.0,
            60.0,
            22.6,
            114.3,
            0.0,
        )
        north = (latitude - 22.6) * 110540.0
        east = (longitude - 114.3) * 111320.0 * __import__("math").cos(
            __import__("math").radians(22.6)
        )
        self.assertAlmostEqual(east, 100.0, places=1)
        self.assertAlmostEqual(north, 200.0, places=1)
        self.assertAlmostEqual(altitude, 60.0)

    def test_route_interpolation_hits_both_ends(self):
        points = ((0.0, 0.0, 10.0), (100.0, 0.0, 20.0))
        self.assertEqual(virtual_rid_tx.route_position(points, 0.0), points[0])
        self.assertEqual(virtual_rid_tx.route_position(points, 1.0), points[1])
        middle = virtual_rid_tx.route_position(points, 0.5)
        self.assertAlmostEqual(middle[0], 50.0)
        self.assertAlmostEqual(middle[2], 15.0)


if __name__ == "__main__":
    unittest.main()
