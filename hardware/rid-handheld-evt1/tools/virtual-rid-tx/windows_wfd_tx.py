"""Broadcast synthetic RID Beacons from a Windows Wi-Fi adapter.

    python windows_wfd_tx.py --path circle --count 8 --interval 8 --yes

Windows cannot inject raw 802.11 frames, but a Wi-Fi Direct autonomous group
owner sends Beacons, and WiFiDirectAdvertisementPublisher lets an application
add vendor information elements to them. RID over Wi-Fi Beacon is exactly such
an element (OUI FA:0B:BC, type 0x0D ASTM / 0xF0 GB 46750).

Paths, origin and identity options are the same as virtual_rid_tx.py. Only the
vendor element payload of each generated frame is used; Windows builds the
Beacon around it from the adapter's own MAC, and the driver picks the channel.

Advertised elements are fixed once a publisher starts (changing them on a live
publisher has no effect on air), so each sample restarts the group owner. On
the tested MT7612U a restart takes 2-5 s and the first seconds after it are
sometimes sparse, so use --interval 8 for every sample to arrive; shorter
intervals drop samples. The receiver marks positions older than 3 s as stale.

Measured on MT7612U / Windows inbox driver 5.1.22: group owner on channel 11,
about 10 Beacons/s once settled. Set CONFIG_RID_CAPTURE_CHANNEL=11 on the P4.

Requires: pip install -r requirements-windows.txt
All identities and positions are synthetic. Use only in a controlled lab.
"""

import sys
import time

import virtual_rid_tx

RID_OUI = b"\xfa\x0b\xbc"


def vendor_payload(frame):
    """Return (type, payload) of the RID vendor element in a Beacon frame."""
    offset = 36
    while offset + 2 <= len(frame):
        element_id = frame[offset]
        length = frame[offset + 1]
        body = frame[offset + 2 : offset + 2 + length]
        if element_id == 221 and body[:3] == RID_OUI and len(body) >= 4:
            return body[3], bytes(body[4:])
        offset += 2 + length
    raise ValueError("frame has no RID vendor element")


def samples(args):
    for index in range(args.count):
        protocol = args.protocol
        if protocol == "both":
            protocol = "gb" if index % 2 == 0 else "astm"
        position = virtual_rid_tx.position_at(args, index)
        frame = virtual_rid_tx.build_frame(
            protocol, index, args.mac, position, int(time.time() * 1000), args
        )
        vendor_type, payload = vendor_payload(frame)
        yield index, position, protocol, vendor_type, payload


class Publisher:
    """One Wi-Fi Direct group owner advertising a single RID element."""

    def __init__(self, ssid):
        from winrt.windows.devices.wifidirect import (
            WiFiDirectAdvertisementListenStateDiscoverability,
            WiFiDirectAdvertisementPublisher,
            WiFiDirectAdvertisementPublisherStatus,
            WiFiDirectInformationElement,
        )
        from winrt.windows.storage.streams import DataWriter

        self._discoverability = WiFiDirectAdvertisementListenStateDiscoverability
        self._publisher_type = WiFiDirectAdvertisementPublisher
        self._element_type = WiFiDirectInformationElement
        self._writer_type = DataWriter
        self._status = WiFiDirectAdvertisementPublisherStatus
        self._ssid = ssid
        self._publisher = None
        self.settle_s = 1.0

    def _buffer(self, data):
        writer = self._writer_type()
        writer.write_bytes(data)
        return writer.detach_buffer()

    def show(self, vendor_type, payload):
        self.stop()
        publisher = self._publisher_type()
        advertisement = publisher.advertisement
        advertisement.is_autonomous_group_owner_enabled = True
        # Any P2P listen state makes the radio leave the group-owner channel,
        # cutting Beacons to short bursts every ~3 s; NONE keeps them at ~10/s.
        advertisement.listen_state_discoverability = self._discoverability.NONE
        advertisement.legacy_settings.is_enabled = True
        advertisement.legacy_settings.ssid = self._ssid
        element = self._element_type()
        element.oui = self._buffer(RID_OUI)
        element.oui_type = vendor_type
        element.value = self._buffer(payload)
        advertisement.information_elements.append(element)
        publisher.start()
        deadline = time.monotonic() + 5.0
        while (publisher.status == self._status.CREATED
               and time.monotonic() < deadline):
            time.sleep(0.05)
        self._publisher = publisher
        if publisher.status == self._status.ABORTED:
            raise SystemExit("Wi-Fi Direct publisher aborted: adapter off or unsupported")
        return publisher.status.name

    def stop(self):
        if self._publisher is None:
            return
        publisher = self._publisher
        self._publisher = None
        publisher.stop()
        # Starting the next group owner before this one is torn down leaves
        # the driver beaconing only in short bursts.
        deadline = time.monotonic() + 5.0
        while (publisher.status != self._status.STOPPED
               and time.monotonic() < deadline):
            time.sleep(0.05)
        time.sleep(self.settle_s)


def main():
    args = virtual_rid_tx.parse_args()
    if not args.dry_run and not args.yes:
        raise SystemExit("Transmission requires --yes")

    publisher = None if args.dry_run else Publisher("DIRECT-RID-TEST")
    try:
        while True:
            started = time.monotonic()
            for index, position, protocol, vendor_type, payload in samples(args):
                status = publisher.show(vendor_type, payload) if publisher else "dry-run"
                print("%02d %s xyz=(%.1f,%.1f,%.1f) %s 0x%02X %d bytes %s" % (
                    index, time.strftime("%H:%M:%S"), *position, protocol,
                    vendor_type, len(payload), status), flush=True)
                if publisher:
                    wait = started + (index + 1) * args.interval - time.monotonic()
                    if wait > 0:
                        time.sleep(wait)
            if not args.loop or args.dry_run:
                break
    finally:
        if publisher:
            publisher.stop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
