# Virtual RID transmitter

The PC can be the controlled RID source, but a normal Windows Wi-Fi driver is
not sufficient. The radio must support monitor mode and raw 802.11 injection.

The connected `0e8d:7612` adapter is a MediaTek MT7612U. On Linux it is
supported by the in-kernel `mt76x2u` driver, including monitor mode and packet
injection. The current Windows driver is a managed-mode Microsoft WLAN driver
and is not suitable for this test.

## Linux setup

Use a Linux machine, a Linux live environment, or a VM with the USB adapter
passed through. Stop NetworkManager from managing the test interface, then:

```bash
sudo ip link set wlan0 down
sudo iw dev wlan0 set type monitor
sudo ip link set wlan0 up
sudo iw dev wlan0 set channel 6
python3 -m pip install scapy
python3 virtual_rid_tx.py --iface wlan0 --protocol both --count 60 --interval 0.5 \
  --path circle --radius 100 --z 60 --duration 20 --yes
```

For the 5 GHz side, configure a reviewed channel such as 149 before running the
same command. Transmit only at low power in a controlled lab environment and
follow local radio regulations.

The script sends IEEE 802.11 Beacon frames under a minimal radiotap header. Each
Beacon contains a vendor IE with OUI `FA:0B:BC`:

- vendor type `0xF0`: generated GB 46750-2025 packet;
- vendor type `0x0D`: generated ASTM/OpenDroneID message pack.

All generated identities and positions are fixtures, not real aircraft.

## Local XYZ motion

The receiver origin defaults to ``(0, 0, 0)`` in local metres. The transmitter
converts each sample to WGS84 around a configured geographic origin:

```text
east  = local x
north = local y
up    = local z
```

Built-in trajectories:

```bash
# 100 m circular orbit at 50-80 m altitude, one lap every 20 s
python3 virtual_rid_tx.py --iface wlan0 --path circle --radius 100 \
  --duration 20 --z 65 --z-amplitude 15 --count 120 --yes

# straight movement along local +Y at 6 m/s
python3 virtual_rid_tx.py --iface wlan0 --path line --vx 0 --vy 6 \
  --z 60 --count 120 --yes

# arbitrary XYZ route, interpolated over each 20-second cycle
python3 virtual_rid_tx.py --iface wlan0 --path route \
  --route "0,0,60;120,0,80;120,120,60;0,120,40" \
  --duration 20 --count 120 --yes
```

Set the geographic anchor with `--origin-lat`, `--origin-lon`, and
`--origin-alt`. The receiver must subtract the same receiver position to
recover local XYZ; raw RID still carries WGS84 latitude, longitude and altitude.

Use `--dry-run` to print the changing XYZ and encoded frame without transmitting.

## Offline check

The frame builder works without Scapy or a radio:

```bash
python3 virtual_rid_tx.py --dry-run --count 2
```
