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

The full real-air loopback is **not yet passed**.

| Check | Result | Evidence |
|---|---|---|
| C6 custom firmware reachable over SDIO | PASS | P4/C6 startup and custom RPC traffic |
| Channel 6 promiscuous capture | PASS | management counter grew beyond 1.8 million |
| ILI9341 initialization | PASS | real panel initialized and firmware remained running |
| C decoder ASTM/GB fixtures | PASS | `C RID decoder fixtures passed` |
| Python RID fixtures | PASS | pure-Python validation suite |
| MT7612U enumerated by Windows | PASS | `0e8d:7612` |
| Host UsbDk reset and vendor register read | PASS | `read_09a8=4` |
| MT7612U enumerated by QEMU guest | PASS | guest saw `0e8d:7612` `802.11ac WLAN` |
| Linux `mt76x2u` probe | FAIL | `vendor request req:07 off:09a8 failed:-110` |
| RID Beacon transmitted | BLOCKED | no live monitor interface |
| Real RID frame received/decoded | BLOCKED | `rid=0 decoded=0` |
| Moving target on panel | BLOCKED | no decoded position available |

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

## Most likely next experiments

1. Re-run on a native Linux host or Linux live boot. This removes Windows
   UsbDk, WHPX, and QEMU from the path and should quickly establish whether the
   adapter can enter monitor mode.
2. If VirtualBox is used, the Extension Pack is required for guest USB 3.0.
   The Oracle PUEL license was not accepted automatically.
3. Review whether a direct UsbDk-backed user-space driver can perform the
   complete `mt76x2u` control sequence without QEMU.
4. After `wlan0` exists, run the command in
   [`../tools/virtual-rid-tx/README.md`](../tools/virtual-rid-tx/README.md).
5. Only mark the loopback complete when all five acceptance conditions pass.

## Important non-claims

- Local UI replay is not real RF reception.
- Decoder fixture tests are not real RF reception.
- USB enumeration in Windows or QEMU is not a successful radio bring-up.
- Receiving unrelated management frames is not RID reception.
- No DJI aircraft identity or position has been received in this validation.
