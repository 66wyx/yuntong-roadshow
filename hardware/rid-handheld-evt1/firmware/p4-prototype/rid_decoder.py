"""RID Wi-Fi vendor-IE decoder for GB 46750-2025 and ASTM/OpenDroneID."""

import struct


OUI_ASD_STAN = b"\xfa\x0b\xbc"
VENDOR_TYPE_ASTM = 0x0D
VENDOR_TYPE_GB46750 = 0xF0

MESSAGE_BASIC_ID = 0
MESSAGE_LOCATION = 1
MESSAGE_AUTH = 2
MESSAGE_SELF_ID = 3
MESSAGE_SYSTEM = 4
MESSAGE_OPERATOR_ID = 5
MESSAGE_PACKED = 15


def _ascii(raw):
    value = bytearray()
    for byte in raw:
        if byte == 0:
            break
        if 0x20 <= byte <= 0x7E:
            value.append(byte)
    return value.decode()


def _u16(data, offset):
    return data[offset] | (data[offset + 1] << 8)


def _u32(data, offset):
    return (
        data[offset]
        | (data[offset + 1] << 8)
        | (data[offset + 2] << 16)
        | (data[offset + 3] << 24)
    )


def _i32(data, offset):
    value = _u32(data, offset)
    return value - 0x100000000 if value & 0x80000000 else value


def _u48(data, offset):
    value = 0
    for index in range(6):
        value |= data[offset + index] << (index * 8)
    return value


def _altitude(raw):
    return None if raw == 0 else raw * 0.5 - 1000.0


def _astm_location(message):
    flags = message[1]
    speed_mult = flags & 0x01
    ew_direction = (flags >> 1) & 0x01
    height_type = (flags >> 2) & 0x01
    status = flags >> 4
    direction = message[2] + (180 if ew_direction else 0)
    speed = message[3] * (0.75 if speed_mult else 0.25)
    if speed_mult:
        speed += 255 * 0.25
    vertical_speed = struct.unpack_from("<b", message, 4)[0] * 0.5
    latitude = _i32(message, 5) / 10_000_000.0
    longitude = _i32(message, 9) / 10_000_000.0
    timestamp_raw = _u16(message, 21)
    return {
        "status": status,
        "direction_deg": direction % 360.0,
        "speed_horizontal_mps": speed,
        "speed_vertical_mps": vertical_speed,
        "latitude": latitude,
        "longitude": longitude,
        "altitude_baro_m": _altitude(_u16(message, 13)),
        "altitude_geo_m": _altitude(_u16(message, 15)),
        "height_m": _altitude(_u16(message, 17)),
        "height_reference": "ground" if height_type else "takeoff",
        "horizontal_accuracy": message[19] & 0x0F,
        "vertical_accuracy": message[19] >> 4,
        "speed_accuracy": message[20] & 0x0F,
        "baro_accuracy": message[20] >> 4,
        "timestamp_in_hour_s": (
            None if timestamp_raw == 0xFFFF else timestamp_raw / 10.0
        ),
        "timestamp_accuracy": message[23] & 0x0F,
        "position_valid": (
            abs(latitude) <= 90
            and abs(longitude) <= 180
            and not (latitude == 0.0 and longitude == 0.0)
        ),
    }


def _astm_system(message):
    flags = message[1]
    latitude = _i32(message, 2) / 10_000_000.0
    longitude = _i32(message, 6) / 10_000_000.0
    return {
        "operator_location_type": flags & 0x03,
        "classification_type": (flags >> 2) & 0x07,
        "operator_latitude": latitude,
        "operator_longitude": longitude,
        "operator_position_valid": (
            abs(latitude) <= 90
            and abs(longitude) <= 180
            and not (latitude == 0.0 and longitude == 0.0)
        ),
        "area_count": _u16(message, 10),
        "area_radius_m": message[12] * 10,
        "area_ceiling_m": _altitude(_u16(message, 13)),
        "area_floor_m": _altitude(_u16(message, 15)),
        "category_eu": message[17] >> 4,
        "class_eu": message[17] & 0x0F,
        "operator_altitude_m": _altitude(_u16(message, 18)),
        "system_timestamp_s": _u32(message, 20),
    }


def decode_odid_message(message):
    if len(message) != 25:
        raise ValueError("OpenDroneID message must be 25 bytes")
    message_type = message[0] >> 4
    version = message[0] & 0x0F
    result = {
        "protocol": "astm_f3411",
        "protocol_version": version,
        "message_type": message_type,
    }
    if message_type == MESSAGE_BASIC_ID:
        result.update(
            {
                "id_type": message[1] >> 4,
                "ua_type": message[1] & 0x0F,
                "uas_id": _ascii(message[2:22]),
            }
        )
    elif message_type == MESSAGE_LOCATION:
        result.update(_astm_location(message))
    elif message_type == MESSAGE_SELF_ID:
        result.update(
            {
                "description_type": message[1],
                "description": _ascii(message[2:25]),
            }
        )
    elif message_type == MESSAGE_SYSTEM:
        result.update(_astm_system(message))
    elif message_type == MESSAGE_OPERATOR_ID:
        result.update(
            {
                "operator_id_type": message[1],
                "operator_id": _ascii(message[2:22]),
            }
        )
    elif message_type == MESSAGE_AUTH:
        result["auth_present"] = True
    return result


def decode_odid_pack(pack):
    if len(pack) < 3 or pack[0] >> 4 != MESSAGE_PACKED:
        raise ValueError("not an OpenDroneID message pack")
    message_size = pack[1]
    message_count = pack[2]
    if message_size != 25 or not 1 <= message_count <= 9:
        raise ValueError("invalid OpenDroneID pack header")
    required = 3 + message_size * message_count
    if len(pack) < required:
        raise ValueError("truncated OpenDroneID pack")
    merged = {
        "protocol": "astm_f3411",
        "protocol_version": pack[0] & 0x0F,
        "message_types": [],
    }
    for index in range(message_count):
        offset = 3 + index * message_size
        decoded = decode_odid_message(pack[offset : offset + message_size])
        merged["message_types"].append(decoded["message_type"])
        for key, value in decoded.items():
            if key not in ("protocol", "protocol_version", "message_type"):
                merged[key] = value
    return merged


def decode_astm_payload(payload):
    if len(payload) >= 2 and payload[1] >> 4 == MESSAGE_PACKED:
        merged = decode_odid_pack(payload[1:])
        merged["message_counter"] = payload[0]
        merged["vendor_payload_hex"] = payload.hex()
        return merged
    if payload and payload[0] >> 4 == MESSAGE_PACKED:
        merged = decode_odid_pack(payload)
        merged["message_counter"] = 0
        merged["vendor_payload_hex"] = payload.hex()
        return merged
    if len(payload) >= 25:
        decoded = decode_odid_message(payload[:25])
        decoded["message_counter"] = 0
        decoded["vendor_payload_hex"] = payload.hex()
        return decoded
    raise ValueError("unsupported ASTM/OpenDroneID payload")


def _gb_latlon(content, offset):
    raw_lon = _u32(content, offset)
    raw_lat = _u32(content, offset + 4)
    if raw_lon == 0xFFFFFFFF or raw_lat == 0xFFFFFFFF:
        return None, None
    return _i32(content, offset + 4) / 1e7, _i32(content, offset) / 1e7


def decode_gb46750_payload(payload):
    if len(payload) < 4 or payload[0] != 0xFF:
        raise ValueError("not a GB 46750 payload")
    version = payload[1]
    content_length = payload[2]
    major = version >> 5
    if major != 1:
        raise ValueError("unsupported GB 46750 major version")

    flags = []
    offset = 3
    while offset < len(payload) and len(flags) < 8:
        flag = payload[offset]
        flags.append(flag)
        offset += 1
        if not (flag & 0x01):
            break
    content_offset = offset
    if content_offset + content_length > len(payload):
        raise ValueError("truncated GB 46750 content")
    content = payload[content_offset : content_offset + content_length]
    result = {
        "protocol": "gb46750_2025",
        "protocol_version": "1.%d" % (version & 0x1F),
        "flags_hex": bytes(flags).hex(),
        "present_fields": [],
        "vendor_payload_hex": payload.hex(),
    }
    cursor = 0
    parsed = 0

    for byte_index, flag in enumerate(flags):
        for bit in range(7, 0, -1):
            if not (flag & (1 << bit)):
                continue
            if byte_index == 0:
                if bit == 7:
                    if cursor + 20 > len(content):
                        raise ValueError("truncated unique ID")
                    result["uas_id"] = _ascii(content[cursor : cursor + 20])
                    result["present_fields"].append("sn")
                    cursor += 20
                elif bit == 6:
                    if cursor + 8 > len(content):
                        raise ValueError("truncated registration ID")
                    result["registration_id"] = _ascii(content[cursor : cursor + 8])
                    result["present_fields"].append("registration")
                    cursor += 8
                elif bit == 5:
                    if cursor >= len(content):
                        raise ValueError("truncated operation category")
                    result["operation_category"] = content[cursor] & 0x0F
                    result["present_fields"].append("operation_category")
                    cursor += 1
                elif bit == 4:
                    if cursor >= len(content):
                        raise ValueError("truncated drone class")
                    result["drone_class"] = content[cursor] & 0x0F
                    result["present_fields"].append("drone_class")
                    cursor += 1
                elif bit == 3:
                    if cursor >= len(content):
                        raise ValueError("truncated operator location type")
                    result["operator_location_type"] = content[cursor] & 0x03
                    result["present_fields"].append("operator_location_type")
                    cursor += 1
                elif bit == 2:
                    if cursor + 8 > len(content):
                        raise ValueError("truncated operator location")
                    lat, lon = _gb_latlon(content, cursor)
                    result["operator_latitude"] = lat
                    result["operator_longitude"] = lon
                    result["operator_position_valid"] = lat is not None and lon is not None
                    result["present_fields"].append("operator_location")
                    cursor += 8
                elif bit == 1:
                    if cursor + 2 > len(content):
                        raise ValueError("truncated operator altitude")
                    raw = _u16(content, cursor)
                    result["operator_altitude_m"] = _altitude(raw)
                    result["present_fields"].append("operator_altitude")
                    cursor += 2
            elif byte_index == 1:
                if bit == 7:
                    if cursor + 8 > len(content):
                        raise ValueError("truncated UAV location")
                    lat, lon = _gb_latlon(content, cursor)
                    result["latitude"] = lat
                    result["longitude"] = lon
                    result["position_valid"] = lat is not None and lon is not None
                    result["present_fields"].append("uav_location")
                    cursor += 8
                elif bit == 6:
                    if cursor + 2 > len(content):
                        raise ValueError("truncated track angle")
                    raw = _u16(content, cursor)
                    result["direction_deg"] = None if raw == 0xFFFF else raw / 10.0
                    result["present_fields"].append("track_angle")
                    cursor += 2
                elif bit == 5:
                    if cursor + 2 > len(content):
                        raise ValueError("truncated ground speed")
                    raw = _u16(content, cursor)
                    result["speed_horizontal_mps"] = (
                        None if raw == 0xFFFF else raw / 10.0
                    )
                    result["present_fields"].append("ground_speed")
                    cursor += 2
                elif bit == 4:
                    if cursor + 2 > len(content):
                        raise ValueError("truncated relative height")
                    raw = _u16(content, cursor)
                    result["height_m"] = None if raw == 0 else raw * 0.5 - 9000
                    result["height_reference"] = "takeoff"
                    result["present_fields"].append("relative_height")
                    cursor += 2
                elif bit == 3:
                    if cursor >= len(content):
                        raise ValueError("truncated vertical speed")
                    raw = content[cursor]
                    magnitude = (raw & 0x7F) * 0.5
                    result["speed_vertical_mps"] = (
                        None if raw == 0xFF else (-magnitude if raw & 0x80 else magnitude)
                    )
                    result["present_fields"].append("vertical_speed")
                    cursor += 1
                elif bit == 2:
                    if cursor + 2 > len(content):
                        raise ValueError("truncated geodetic altitude")
                    result["altitude_geo_m"] = _altitude(_u16(content, cursor))
                    result["present_fields"].append("geodetic_altitude")
                    cursor += 2
                elif bit == 1:
                    if cursor + 2 > len(content):
                        raise ValueError("truncated barometric altitude")
                    result["altitude_baro_m"] = _altitude(_u16(content, cursor))
                    result["present_fields"].append("barometric_altitude")
                    cursor += 2
            elif byte_index == 2:
                if bit == 7:
                    if cursor >= len(content):
                        raise ValueError("truncated operation status")
                    result["status"] = content[cursor] & 0x0F
                    result["present_fields"].append("operation_status")
                    cursor += 1
                elif bit == 6:
                    if cursor >= len(content):
                        raise ValueError("truncated coordinate system")
                    result["coordinate_system"] = content[cursor] & 0x0F
                    result["present_fields"].append("coordinate_system")
                    cursor += 1
                elif bit == 5:
                    if cursor >= len(content):
                        raise ValueError("truncated horizontal accuracy")
                    result["horizontal_accuracy"] = content[cursor] & 0x0F
                    result["present_fields"].append("horizontal_accuracy")
                    cursor += 1
                elif bit == 4:
                    if cursor >= len(content):
                        raise ValueError("truncated vertical accuracy")
                    result["vertical_accuracy"] = content[cursor] & 0x0F
                    result["present_fields"].append("vertical_accuracy")
                    cursor += 1
                elif bit == 3:
                    if cursor >= len(content):
                        raise ValueError("truncated speed accuracy")
                    result["speed_accuracy"] = content[cursor] & 0x0F
                    result["present_fields"].append("speed_accuracy")
                    cursor += 1
                elif bit == 2:
                    if cursor + 6 > len(content):
                        raise ValueError("truncated timestamp")
                    result["timestamp_unix_ms"] = _u48(content, cursor)
                    result["present_fields"].append("timestamp")
                    cursor += 6
                elif bit == 1:
                    if cursor >= len(content):
                        raise ValueError("truncated timestamp accuracy")
                    result["timestamp_accuracy"] = content[cursor] & 0x0F
                    result["present_fields"].append("timestamp_accuracy")
                    cursor += 1
            parsed += 1
    if not parsed:
        raise ValueError("GB 46750 packet contains no data fields")
    if cursor != len(content):
        result["trailing_content_bytes"] = len(content) - cursor
    return result


def decode_vendor_payload(vendor_type, payload):
    if vendor_type == VENDOR_TYPE_GB46750:
        return decode_gb46750_payload(payload)
    if vendor_type == VENDOR_TYPE_ASTM:
        return decode_astm_payload(payload)
    raise ValueError("unsupported RID vendor type 0x%02x" % vendor_type)


def extract_rid_ies(frame):
    if len(frame) < 38:
        return []
    frame_control = frame[0] | (frame[1] << 8)
    if frame_control & 0x000C:
        return []
    subtype = (frame_control >> 4) & 0x0F
    if subtype not in (5, 8):
        return []
    source_mac = bytes(frame[10:16]).hex(":")
    found = []
    offset = 36
    while offset + 2 <= len(frame):
        element_id = frame[offset]
        length = frame[offset + 1]
        end = offset + 2 + length
        if end > len(frame):
            break
        if (
            element_id == 221
            and length >= 4
            and bytes(frame[offset + 2 : offset + 5]) == OUI_ASD_STAN
        ):
            vendor_type = frame[offset + 5]
            found.append(
                {
                    "source_mac": source_mac,
                    "vendor_type": vendor_type,
                    "payload": bytes(frame[offset + 6 : end]),
                }
            )
        offset = end
    return found


def decode_wifi_frame(frame, rssi=None, channel=None, now_ms=0):
    observations = []
    for record in extract_rid_ies(frame):
        try:
            decoded = decode_vendor_payload(record["vendor_type"], record["payload"])
        except ValueError:
            continue
        decoded["source_mac"] = record["source_mac"]
        decoded["rssi_dbm"] = rssi
        decoded["channel"] = channel
        decoded["received_ms"] = now_ms
        decoded["source"] = "wifi_beacon"
        decoded["decoded"] = True
        observations.append(decoded)
    return observations
