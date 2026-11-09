# ESP32-P4 real-air RID receiver

This is the bench receiver used to validate the ESP32-P4 + ESP32-C6 bring-up.
It listens in promiscuous mode on Wi-Fi channel 6, recognizes RID vendor
elements, decodes ASTM/OpenDroneID and GB 46750-2025 observations, maintains
target state, and renders the radar/height UI on an ILI9341V panel.

This directory is bench validation firmware. It is not yet the EVT1 production
firmware.

## Dependencies

- ESP-IDF 5.5
- `espressif/esp_hosted` 2.11.7
- `espressif/esp_wifi_remote` 1.6.5
- Custom C6 firmware from [`../c6`](../c6), normally installed through
  [`../c6-ota`](../c6-ota)

## Build and monitor

```bash
idf.py set-target esp32p4
idf.py build
idf.py -p /dev/ttyACM0 flash monitor
```

On Windows the tested port was `COM3`:

```powershell
idf.py -p COM3 flash monitor
```

At boot the firmware prints:

```text
RID capture active on channel 6
stats mgmt=<n> rid=<n> decoded=<n>
```

For a valid RID frame it prints `RID_FRAME` followed by `RID_TARGET`, including
protocol, identity, source MAC, WGS84 position, barometric/geometric altitude,
relative height, and receiver-local XYZ.

## Display wiring

The tested module is LCDWiki MSP2834: ILI9341V, 240 x 320, with an ST7796
compatible timing path retained only as an alternative.

| LCDWiki signal | ESP32-P4 |
|---|---|
| VCC | 5 V / VBUS |
| GND | GND |
| LCD_CS | GPIO20 |
| LCD_RST | GPIO21 |
| LCD_RS / DC | GPIO22 |
| SDI / MOSI | GPIO23 |
| SCK | GPIO26 |
| LED / BL | GPIO27 |
| SDO / MISO | GPIO32 |
| SD_CS | Not connected |

The FT6336G touch controller is intentionally not part of this firmware's
acceptance path. The display and all RID UI checks are touchless.

## Host-side decoder checks

```bash
gcc -shared -fPIC -O2 -Imain main/rid_decoder.c -o /tmp/librid_decoder.so
python3 tools/test_rid_decoder.py /tmp/librid_decoder.so
```

Expected output:

```text
C RID decoder fixtures passed
```

Passing fixtures validates protocol parsing only. It is not evidence of a
real-air RID reception.

## Current evidence

- The real P4/C6 link started successfully over SDIO.
- Channel 6 promiscuous capture counted more than 1.8 million management
  frames across a long bench run.
- No RID frame was observed because the PC transmitter did not complete the
  MT7612U monitor-mode initialization in the tested QEMU path.
- The C decoder fixtures passed.
- The ILI9341 initialization succeeded on the bench panel; actual decoded
  aircraft rendering still awaits a successful transmitter.

See [`../../validation/REAL_AIR_LOOPBACK_HANDOFF.md`](../../validation/REAL_AIR_LOOPBACK_HANDOFF.md)
for the full evidence and remaining blocker.
