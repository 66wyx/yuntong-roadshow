# Virtual RID transmitter

`virtual_rid_tx.py` builds deterministic IEEE 802.11 Beacon frames containing
GB 46750-2025 or ASTM/OpenDroneID vendor elements and injects them through a
Linux monitor-mode interface.

Install the Python dependency:

```bash
python3 -m pip install -r requirements.txt
```

Prepare the MT7612U under Linux:

```bash
sudo ip link set wlan0 down
sudo iw dev wlan0 set type monitor
sudo ip link set wlan0 up
sudo iw dev wlan0 set channel 6
```

Run the receiver-local route:

```bash
sudo python3 virtual_rid_tx.py \
  --iface wlan0 \
  --protocol both \
  --count 120 \
  --interval 0.25 \
  --path route \
  --route "0,0,0;100,0,20;100,100,60;0,100,30;0,0,0" \
  --duration 20 \
  --origin-lat 22.6000000 \
  --origin-lon 114.3000000 \
  --origin-alt 0 \
  --yes
```

The receiver's geographic anchor is fixed at latitude `22.6000000`, longitude
`114.3000000`, altitude `0` (`rid_receiver_anchor` in
`firmware/p4/main/rid_geo.c`); local XYZ maps to east, north, and up. Z is
encoded as geodetic altitude `origin-alt + z`, which the receiver turns back
into height relative to itself.

Each frame also carries a ground track and speed computed from the path. With
`--protocol both`, GB and ASTM frames share one `--uas-id`
(default `LAB-TEST-001`), so the receiver shows one aircraft.

Run the tests with `python3 -m unittest -v test_rid_validation`.

## Windows transmitter (no monitor mode)

`windows_wfd_tx.py` takes the same path and identity options but sends through
a Windows Wi-Fi Direct group owner. Windows builds the Beacon and adds the RID
vendor element to it. No VM, monitor mode, or administrator rights are needed.

```powershell
python -m pip install -r requirements-windows.txt
python windows_wfd_tx.py --path circle --radius 100 --z 60 --z-amplitude 20 `
  --duration 64 --count 8 --interval 8 --protocol both --yes
```

The driver chooses the channel; the tested MT7612U used channel 11. Build the
P4 with `CONFIG_RID_CAPTURE_CHANNEL=11`. If the channel is unknown, set
`CONFIG_RID_SCAN_DWELL_MS` to hop 1/6/11 and read `ch=` from `RID_FRAME`.

Each position restarts the group owner, which takes 2–5 s. Use `--interval 8`
so every position is received. The target moves in steps, and is shown as
stale between steps.

Measured 2026-11-05 on the bench: 8 of 8 circle positions decoded on the P4,
alternating GB 46750 and ASTM, `LAB-TEST-001`, XYZ matching the transmitter to
0.1 m, RSSI about −19 dBm.

Use `--dry-run` to inspect changing XYZ samples and encoded frames without a
radio.

All identities and positions are synthetic. Transmit only at low power in a
controlled lab and follow local radio regulations.
