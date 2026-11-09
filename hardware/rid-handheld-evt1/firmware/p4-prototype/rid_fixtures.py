"""Deterministic Wi-Fi frames used only for decoder and UI replay tests."""


OUI = b"\xfa\x0b\xbc"


def _ascii_field(text, size):
    raw = text.encode()[:size]
    return raw + b"\x00" * (size - len(raw))


def _u16(value):
    value = max(0, min(0xFFFF, int(value)))
    return bytes((value & 0xFF, value >> 8))


def _i32(value):
    value = int(value) & 0xFFFFFFFF
    return bytes(
        (
            value & 0xFF,
            (value >> 8) & 0xFF,
            (value >> 16) & 0xFF,
            (value >> 24) & 0xFF,
        )
    )


def _u48(value):
    return bytes((value >> (index * 8)) & 0xFF for index in range(6))


def _astm_altitude(value):
    if value is None:
        return _u16(0)
    return _u16(round((value + 1000.0) * 2.0))


def _beacon(source_mac, vendor_ie):
    header = bytearray(24)
    header[0] = 0x80
    header[4:10] = b"\xff\xff\xff\xff\xff\xff"
    header[10:16] = source_mac
    header[16:22] = source_mac
    fixed = b"\x00" * 8 + b"\x64\x00" + b"\x31\x04"
    ssid = b"\x00\x08RID-TEST"
    rates = b"\x01\x01\x8c"
    return bytes(header) + fixed + ssid + rates + vendor_ie


def _vendor_ie(vendor_type, payload):
    content = OUI + bytes((vendor_type,)) + payload
    return b"\xdd" + bytes((len(content),)) + content


def astm_frame(
    source_mac=b"\x02\x00\x00\x00\x00\x01",
    uas_id="LAB-TEST-001",
    latitude=22.6000,
    longitude=114.3000,
    altitude_geo=125.0,
    height=62.0,
    counter=0,
    track_deg=90.0,
    speed_mps=40.0,
):
    basic = bytearray(25)
    basic[0] = 0x02
    basic[1] = 0x12
    basic[2:22] = _ascii_field(uas_id, 20)

    location = bytearray(25)
    location[0] = 0x12
    track = int(round(track_deg)) % 360
    east_west = track >= 180
    speed_multiplier = speed_mps > 255 * 0.25
    speed_raw = (
        (speed_mps - 255 * 0.25) / 0.75 if speed_multiplier else speed_mps / 0.25
    )
    location[1] = 0x20 | (0x02 if east_west else 0) | (0x01 if speed_multiplier else 0)
    location[2] = track - 180 if east_west else track
    location[3] = max(0, min(254, int(round(speed_raw))))
    location[4] = 4
    location[5:9] = _i32(round(latitude * 10_000_000))
    location[9:13] = _i32(round(longitude * 10_000_000))
    location[13:15] = _astm_altitude(120.0)
    location[15:17] = _astm_altitude(altitude_geo)
    location[17:19] = _astm_altitude(height)
    location[19] = 0x6C
    location[20] = 0x64
    location[21:23] = _u16(123)
    location[23] = 0x08

    system = bytearray(25)
    system[0] = 0x42
    system[1] = 0x01
    system[2:6] = _i32(round(22.5990 * 10_000_000))
    system[6:10] = _i32(round(114.2990 * 10_000_000))
    system[10:12] = _u16(1)
    system[12] = 10
    system[13:15] = _astm_altitude(200.0)
    system[15:17] = _astm_altitude(0.0)
    system[17] = 0x00
    system[18:20] = _astm_altitude(84.0)

    operator = bytearray(25)
    operator[0] = 0x52
    operator[1] = 0
    operator[2:22] = _ascii_field("DEMO-OPERATOR", 20)

    messages = bytes(basic + location + system + operator)
    pack = bytes((0xF2, 25, 4)) + messages
    payload = bytes((counter & 0xFF,)) + pack
    return _beacon(source_mac, _vendor_ie(0x0D, payload))


def _gb_altitude(value):
    if value is None:
        return _u16(0)
    return _u16(round((value + 1000.0) * 2.0))


def _gb_relative_altitude(value):
    if value is None:
        return _u16(0)
    return _u16(round((value + 9000.0) * 2.0))


def gb46750_frame(
    source_mac=b"\x02\x00\x00\x00\x00\x02",
    uas_id="GB-DEMO-002",
    registration_id="UAS00002",
    latitude=22.5987,
    longitude=114.3012,
    altitude_geo=155.0,
    height=75.0,
    timestamp_ms=1_800_000_000_000,
    track_deg=27.5,
    speed_mps=8.8,
):
    content = bytearray()
    content.extend(_ascii_field(uas_id, 20))
    content.extend(_ascii_field(registration_id, 8))
    content.append(1)
    content.append(1)
    content.append(1)
    content.extend(_i32(round(114.2995 * 10_000_000)))
    content.extend(_i32(round(22.5992 * 10_000_000)))
    content.extend(_gb_altitude(85.0))
    content.extend(_i32(round(longitude * 10_000_000)))
    content.extend(_i32(round(latitude * 10_000_000)))
    content.extend(_u16(round((track_deg % 360.0) * 10)))
    content.extend(_u16(round(speed_mps * 10)))
    content.extend(_gb_relative_altitude(height))
    content.append(0x02)
    content.extend(_gb_altitude(altitude_geo))
    content.extend(_gb_altitude(150.0))
    content.append(2)
    content.append(0)
    content.append(12)
    content.append(6)
    content.append(4)
    content.extend(_u48(timestamp_ms))
    content.append(7)

    flags = b"\xff\xff\xfe"
    payload = b"\xff\x20" + bytes((len(content),)) + flags + bytes(content)
    return _beacon(source_mac, _vendor_ie(0xF0, payload))

