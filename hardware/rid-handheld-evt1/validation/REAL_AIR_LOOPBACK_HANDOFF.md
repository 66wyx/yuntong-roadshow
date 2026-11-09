# Real-air RID loopback handoff

Date: 2026-11-05

## Objective under test

Use a PC MT7612U to transmit synthetic RID Beacons whose XYZ position follows a
route, decode them on the real ESP32-P4/C6 receiver, and display moving targets
on the ILI9341 panel.

The required acceptance sequence is:

1. PC monitor interface continuously transmits.
2. P4 UART reports `RID_FRAME`.
3. P4 UART reports `RID_TARGET` with changing XYZ.
4. Receiver counters show `rid>0` and `decoded>0`.
5. The panel shows the moving target and matching XYZ/height.

## Status at this commit

The real-air loopback **passes** with a Windows Wi-Fi Direct source (see
below): RID is received and decoded, and the moving target is shown on the
panel. This is not the monitor-mode injection path originally planned.

| Check | Result | Evidence |
|---|---|---|
| C6 custom firmware reachable over SDIO | PASS | P4/C6 startup and custom RPC traffic |
| Channel 6 promiscuous capture | PASS | management counter grew beyond 1.8 million |
| ILI9341 initialization | PASS | real panel initialized and firmware remained running |
| Previous UI drawing | FAIL | circles drew as tall ovals; 10 CJK glyphs missing |
| Redesigned UI on host | PASS | `P4 host checks passed`; see [`../firmware/p4/docs/ui`](../firmware/p4/docs/ui) |
| Redesigned UI on panel | PASS | flashed, waiting and live screens checked by eye; `ui_us` 72–80 ms |
| C decoder ASTM/GB fixtures | PASS | `C RID decoder fixtures passed`, incl. westerly tracks |
| Python RID fixtures | PASS | pure-Python validation suite |
| MT7612U enumerated by Windows | PASS | `0e8d:7612` |
| Host UsbDk reset and vendor register read | PASS | `read_09a8=4` |
| MT7612U enumerated by QEMU guest | PASS | guest saw `0e8d:7612` `802.11ac WLAN` |
| Linux `mt76x2u` probe | FAIL | `vendor request req:07 off:09a8 failed:-110` |
| RID Beacon transmitted (monitor mode) | BLOCKED | no live monitor interface |
| RID Beacon transmitted (Windows Wi-Fi Direct) | PASS | `windows_wfd_tx.py`, group owner on channel 11 |
| Real RID frame received/decoded | PASS | `rid=1232 decoded=1232`, GB and ASTM, `ch=11 rssi≈-19` |
| Continuous looping transmission | PASS | multi-lap circle run, counters rising, target moving on panel |
| `RID_TARGET` with changing XYZ | PASS | 8/8 circle positions, XYZ equal to transmitter |
| Moving target on panel | PASS | confirmed by eye on the ILI9341 during a looping circle run |

## Windows Wi-Fi Direct loopback (2026-11-05)

Source: MT7612U on the Windows inbox driver, no VM. The PC ran
[`../tools/virtual-rid-tx/windows_wfd_tx.py`](../tools/virtual-rid-tx/windows_wfd_tx.py),
which adds the RID vendor element to a Wi-Fi Direct group owner's Beacons. The
P4 was built with `CONFIG_RID_CAPTURE_CHANNEL=11`.

```text
tx gb   xyz=100,0,60    -> gb46750_2025 LAB-TEST-001 x61
tx astm xyz=71,71,80    -> astm_f3411 LAB-TEST-001 x30
tx gb   xyz=0,100,60    -> gb46750_2025 LAB-TEST-001 x29
tx astm xyz=-71,71,40   -> astm_f3411 LAB-TEST-001 x30
tx gb   xyz=-100,0,60   -> gb46750_2025 LAB-TEST-001 x4
tx astm xyz=-71,-71,80  -> astm_f3411 LAB-TEST-001 x31
tx gb   xyz=0,-100,60   -> gb46750_2025 LAB-TEST-001 x31
tx astm xyz=71,-71,40   -> astm_f3411 LAB-TEST-001 x29
received 8/8 samples
```

Findings:

- The group owner sits on channel 11, not 6. Nothing was received until the P4
  capture channel was changed.
- With the default P2P listen state the radio leaves channel 11, and Beacons
  arrive only in bursts of 3 every ~3 s. `listen_state_discoverability = NONE`
  gives a steady ~10/s.
- Vendor elements cannot be changed on a running publisher; each position
  restarts it, costing 2–5 s. Sustained rate even with one publisher
  occasionally falls back to bursts. An 8 s interval delivered every position;
  6 s lost 2 of 8.
- Source MAC is the adapter's Wi-Fi Direct address (`0a:13:ef:3f:65:d5`), not
  `--mac`.

## Observed receiver health

A long bench run showed management frames arriving continuously:

```text
stats mgmt=1750070 rid=0 decoded=0
stats mgmt=1813398 rid=0 decoded=0
```

This proves the P4/C6 promiscuous path is active. The zero RID count is expected
while no RID source is transmitting.

## Transmitter blocker

The Windows host can talk to the MT7612U through UsbDk:

```text
device_count=8
usb=1.25 id=0e8d:7612
open=0
reset_device=0
claim_interface_0=0
read_09a8=4
```

QEMU passes the real device to Ubuntu and Linux recognizes it:

```text
usb 1-1: New USB device found, idVendor=0e8d, idProduct=7612
usb 1-1: Product: 802.11ac WLAN
```

The `mt76x2u` probe then times out:

```text
mt76x2u 1-1:1.0: vendor request req:07 off:09a8 failed:-110
mt76x2u 1-1:1.0: vendor request req:06 off:09a8 failed:-110
mt76x2u 1-1:1.0: vendor request req:42 off:0230 failed:-110
```

Tests performed:

- Direct USB/IP to WSL: same early control-transfer timeout.
- QEMU xHCI passthrough: same failure.
- QEMU EHCI passthrough: same failure.
- `guest-reset` enabled and disabled: same failure.
- QEMU `pipeline=off`: same failure.
- UsbDk selected explicitly through a libusb proxy: guest enumeration passes,
  driver register access still fails.
- Synchronous control-transfer proxy and reset settle delay: source committed,
  but a final confirmation run is blocked by a stuck Windows QEMU/WHPX process
  retaining the virtual disk and UsbDk redirector.

## Next steps

All five acceptance conditions now pass with the Windows Wi-Fi Direct source.
Remaining work, in priority order:

1. **Real aircraft.** Capture a real DJI or other RID broadcast on channel 6
   with the default build and keep the raw `RID_FRAME` hex as an external test
   vector. The decoders are still only checked against this repository's own
   fixtures.
2. **Receiver load.** The C6 forwards every management frame over SDIO, and
   the P4 prints full frame hex in the RX callback. Filter on the C6 to frames
   with the `FA:0B:BC` vendor element, and move logging off the receive path.
3. **Faster bench source.** Monitor-mode injection would give continuous
   motion instead of 8 s steps. Options: a native Linux host or live boot, or a
   second ESP32 using `WIFI_RAW_MSG_80211_TX`, which the C6 already supports.
4. **Panel timing.** `ui_us` is 72–80 ms per frame, mostly the 20 MHz SPI
   flush. Use DMA or partial flushes before adding input handling.

Measured on the bench: the main task did not overflow with an 8 KB stack.
Stack high-water mark has not been recorded.

## Receiver fixes after review

- ASTM ground track: `raw + 180` overflowed `uint8_t`, so every westerly track
  (180–359°) decoded wrong, e.g. 270° became 14°.
- Relative height now means target geodetic altitude minus receiver altitude.
  The broadcast `height` (above take-off/ground) is no longer shown as relative
  height. Both happen to match for `--origin-alt 0`, which hid the bug.
- ASTM Operator ID is stored separately and never used as the aircraft ID.
- Validity flags for altitude, height, track, and speed. Unknown values show as
  `—` and are not drawn as 0.
- `wait_cmd_response` ignores late replies to earlier commands instead of
  returning their status.
- Main task stack raised to 8 KB for the new renderer.
- Transmitter: GB and ASTM frames share one `--uas-id` and carry the path's
  real track and speed.

## Important non-claims

- Local UI replay is not real RF reception.
- Decoder fixture tests are not real RF reception.
- USB enumeration in Windows or QEMU is not a successful radio bring-up.
- Receiving unrelated management frames is not RID reception.
- No DJI aircraft identity or position has been received in this validation.
