"""Observable-first RID target state with independent identity and position age."""


def _finite_number(value):
    return isinstance(value, (int, float)) and value == value


class TargetStore:
    def __init__(self, position_stale_ms=3000, target_expire_ms=10000):
        self.position_stale_ms = position_stale_ms
        self.target_expire_ms = target_expire_ms
        self.targets = {}
        self.mac_to_key = {}

    def _find_key(self, observation):
        mac = observation.get("source_mac")
        if mac and mac in self.mac_to_key:
            return self.mac_to_key[mac]
        identity = observation.get("uas_id") or observation.get("registration_id")
        if identity:
            for key, target in self.targets.items():
                if target.get("uas_id") == identity:
                    return key
        return None

    def apply(self, observation, now_ms):
        key = self._find_key(observation)
        if key is None:
            identity = (
                observation.get("uas_id")
                or observation.get("registration_id")
                or observation.get("source_mac")
                or "unknown"
            )
            key = observation.get("protocol", "rid") + ":" + identity
            if key in self.targets:
                suffix = 2
                base = key
                while key in self.targets:
                    key = base + "#" + str(suffix)
                    suffix += 1
            self.targets[key] = {
                "key": key,
                "first_seen_ms": now_ms,
                "last_seen_ms": now_ms,
                "last_position_ms": None,
                "message_count": 0,
                "protocol": observation.get("protocol", "unknown"),
                "uas_id": None,
                "registration_id": None,
                "latitude": None,
                "longitude": None,
                "position_valid": False,
            }

        target = self.targets[key]
        target["last_seen_ms"] = now_ms
        target["message_count"] += 1
        if observation.get("source_mac"):
            self.mac_to_key[observation["source_mac"]] = key
            target["source_mac"] = observation["source_mac"]
        if observation.get("rssi_dbm") is not None:
            target["rssi_dbm"] = observation["rssi_dbm"]
        if observation.get("channel") is not None:
            target["channel"] = observation["channel"]

        copied = (
            "uas_id",
            "registration_id",
            "ua_type",
            "id_type",
            "drone_class",
            "operation_category",
            "status",
            "coordinate_system",
            "direction_deg",
            "speed_horizontal_mps",
            "speed_vertical_mps",
            "altitude_geo_m",
            "altitude_baro_m",
            "height_m",
            "height_reference",
            "operator_latitude",
            "operator_longitude",
            "operator_position_valid",
            "operator_altitude_m",
            "operator_location_type",
            "operator_id",
            "description",
            "horizontal_accuracy",
            "vertical_accuracy",
            "speed_accuracy",
            "timestamp_accuracy",
            "timestamp_unix_ms",
            "timestamp_in_hour_s",
            "message_counter",
            "source",
            "vendor_payload_hex",
        )
        for field in copied:
            if field in observation and observation[field] is not None:
                target[field] = observation[field]

        latitude = observation.get("latitude")
        longitude = observation.get("longitude")
        if (
            observation.get("position_valid")
            and _finite_number(latitude)
            and _finite_number(longitude)
        ):
            target["latitude"] = latitude
            target["longitude"] = longitude
            target["position_valid"] = True
            target["last_position_ms"] = now_ms
        return target

    def get(self, key):
        return self.targets.get(key)

    def age_ms(self, target, now_ms):
        return max(0, now_ms - target["last_seen_ms"])

    def position_age_ms(self, target, now_ms):
        if target.get("last_position_ms") is None:
            return None
        return max(0, now_ms - target["last_position_ms"])

    def state(self, target, now_ms):
        age = self.age_ms(target, now_ms)
        if age > self.target_expire_ms:
            return "expired"
        position_age = self.position_age_ms(target, now_ms)
        if position_age is None:
            return "identity_only"
        if position_age > self.position_stale_ms:
            return "stale"
        return "active"

    def snapshot(self, now_ms):
        result = []
        for target in self.targets.values():
            item = dict(target)
            item["age_ms"] = self.age_ms(target, now_ms)
            item["position_age_ms"] = self.position_age_ms(target, now_ms)
            item["state"] = self.state(target, now_ms)
            result.append(item)
        result.sort(key=lambda item: item["last_seen_ms"], reverse=True)
        return result

    def active_positions(self, now_ms):
        return [
            target
            for target in self.snapshot(now_ms)
            if target["state"] == "active" and target.get("position_valid")
        ]
