"""Transmit generated GB 46750/ASTM RID Beacons from a Linux monitor interface."""

import argparse
import math
import time

import rid_fixtures


def parse_mac(value):
    parts = value.replace("-", ":").split(":")
    if len(parts) != 6:
        raise argparse.ArgumentTypeError("MAC must contain 6 octets")
    try:
        return bytes(int(part, 16) for part in parts)
    except ValueError:
        raise argparse.ArgumentTypeError("invalid MAC address")


def parse_route(value):
    points = []
    for item in value.split(";"):
        coordinates = [float(part) for part in item.split(",")]
        if len(coordinates) != 3:
            raise argparse.ArgumentTypeError("route points require x,y,z")
        points.append(tuple(coordinates))
    if len(points) < 2:
        raise argparse.ArgumentTypeError("route requires at least two points")
    return points


def local_to_wgs84(x, y, z, origin_lat, origin_lon, origin_alt):
    latitude = origin_lat + y / 110540.0
    longitude = origin_lon + x / (
        111320.0 * math.cos(math.radians(origin_lat))
    )
    return latitude, longitude, origin_alt + z


def route_position(points, phase):
    lengths = []
    total = 0.0
    for index in range(len(points) - 1):
        start = points[index]
        end = points[index + 1]
        length = math.sqrt(
            (end[0] - start[0]) ** 2
            + (end[1] - start[1]) ** 2
            + (end[2] - start[2]) ** 2
        )
        lengths.append(length)
        total += length
    target = total * phase
    for index, length in enumerate(lengths):
        if target <= length or index == len(lengths) - 1:
            ratio = 0.0 if length == 0 else target / length
            start = points[index]
            end = points[index + 1]
            return (
                start[0] + (end[0] - start[0]) * ratio,
                start[1] + (end[1] - start[1]) * ratio,
                start[2] + (end[2] - start[2]) * ratio,
            )
        target -= length
    return points[-1]


def position_at(args, index):
    elapsed = index * args.interval
    if args.path == "stationary":
        return args.x, args.y, args.z
    if args.path == "line":
        seconds = (
            (elapsed % args.duration) / args.duration * args.duration
            if args.loop and args.duration > 0
            else elapsed
        )
        return (
            args.x + args.vx * seconds,
            args.y + args.vy * seconds,
            args.z + args.vz * seconds,
        )
    phase = 0.0 if args.duration <= 0 else (elapsed % args.duration) / args.duration
    if args.path == "circle":
        angle = phase * math.tau
        return (
            args.radius * math.cos(angle),
            args.radius * math.sin(angle),
            args.z + args.z_amplitude * math.sin(angle * 2.0),
        )
    return route_position(args.route, phase)


def build_frame(protocol, index, mac, position, timestamp_ms, args):
    x, y, z = position
    latitude, longitude, altitude = local_to_wgs84(
        x,
        y,
        z,
        args.origin_lat,
        args.origin_lon,
        args.origin_alt,
    )
    if protocol == "gb":
        return rid_fixtures.gb46750_frame(
            source_mac=mac,
            latitude=latitude,
            longitude=longitude,
            altitude_geo=altitude,
            height=max(0.0, z),
            timestamp_ms=timestamp_ms,
        )
    return rid_fixtures.astm_frame(
        source_mac=mac,
        latitude=latitude,
        longitude=longitude,
        altitude_geo=altitude,
        height=max(0.0, z),
        counter=index & 0xFF,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--iface", default="wlan0")
    parser.add_argument("--protocol", choices=("both", "gb", "astm"), default="both")
    parser.add_argument("--count", type=int, default=60)
    parser.add_argument("--interval", type=float, default=0.5)
    parser.add_argument("--mac", type=parse_mac, default=parse_mac("02:00:00:00:01:00"))
    parser.add_argument("--origin-lat", type=float, default=22.6000000)
    parser.add_argument("--origin-lon", type=float, default=114.3000000)
    parser.add_argument("--origin-alt", type=float, default=0.0)
    parser.add_argument(
        "--path", choices=("stationary", "line", "circle", "route"), default="circle"
    )
    parser.add_argument("--duration", type=float, default=20.0)
    parser.add_argument("--radius", type=float, default=80.0)
    parser.add_argument("--x", type=float, default=0.0)
    parser.add_argument("--y", type=float, default=0.0)
    parser.add_argument("--z", type=float, default=60.0)
    parser.add_argument("--vx", type=float, default=0.0)
    parser.add_argument("--vy", type=float, default=6.0)
    parser.add_argument("--vz", type=float, default=0.0)
    parser.add_argument("--z-amplitude", type=float, default=0.0)
    parser.add_argument(
        "--route",
        type=parse_route,
        default=parse_route("0,0,60;120,0,80;120,120,60;0,120,40"),
    )
    parser.add_argument("--loop", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--yes", action="store_true")
    args = parser.parse_args()

    if not args.dry_run and not args.yes:
        raise SystemExit("Transmission requires --yes after monitor mode is configured")

    for index in range(args.count):
        selected = args.protocol
        if selected == "both":
            selected = "gb" if index % 2 == 0 else "astm"
        position = position_at(args, index)
        packet = build_frame(
            selected,
            index,
            args.mac,
            position,
            int(time.time() * 1000) + int(index * args.interval * 1000),
            args,
        )
        if args.dry_run:
            print(
                "%02d xyz=(%.2f,%.2f,%.2f) %d %s"
                % (index, position[0], position[1], position[2], len(packet), packet.hex())
            )
            continue

    if args.dry_run:
        return

    try:
        from scapy.all import RadioTap, Raw, sendp
    except ImportError:
        raise SystemExit("Scapy is required: python3 -m pip install scapy")

    started = time.monotonic()
    for index in range(args.count):
        selected = args.protocol
        if selected == "both":
            selected = "gb" if index % 2 == 0 else "astm"
        elapsed = index * args.interval
        position = position_at(args, index)
        packet = build_frame(
            selected,
            index,
            args.mac,
            position,
            int(time.time() * 1000),
            args,
        )
        sendp(RadioTap() / Raw(packet), iface=args.iface, verbose=False)
        print(
            "tx %02d xyz=(%.1f,%.1f,%.1f) %s"
            % (index, position[0], position[1], position[2], selected)
        )
        wait = started + (index + 1) * args.interval - time.monotonic()
        if wait > 0:
            time.sleep(wait)
    print("sent %d frames on %s" % (args.count, args.iface))


if __name__ == "__main__":
    main()
