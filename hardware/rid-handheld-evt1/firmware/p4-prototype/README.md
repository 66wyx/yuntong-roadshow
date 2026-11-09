# EVT0 validation rig: display and touch

This test leaves the existing MicroPython firmware and `boot.py` in place.
The physical module is the LCDWiki MSP2834: ILI9341V display with FT6336G
capacitive touch (`0x38`). An ST7789 driver is retained only for comparison.
It does not install a `main.py` or change the boot sequence.

## Wiring

Use the header GPIO names printed on the ESP32-P4-WIFI6 board. The official
MSP2834 specification gives `VCC = 5.0 V`; its onboard level shifter keeps the
SPI/I2C signal levels compatible with the P4's 3.3 V logic.

| 2.8-inch LCD | ESP32-P4 |
|---|---|
| VCC | 5V / VBUS |
| GND | GND |
| LCD_CS | GPIO20 |
| LCD_RST | GPIO21 |
| LCD_RS / DC | GPIO22 |
| SDI / MOSI | GPIO23 |
| SCK | GPIO26 |
| LED / BL | GPIO27 |
| SDO / MISO (optional) | GPIO32 |
| CTP_SCL | GPIO8 |
| CTP_RST | GPIO46 |
| CTP_SDA | GPIO7 |
| CTP_INT | GPIO48 |
| SD_CS | Not connected |

`CTP_INT` is not required by the polling test. The P4 board already has its own
SDIO microSD slot; do not confuse it with this LCD board's `SD_CS`.

## Run

With the current MicroPython firmware on `COM3`:

```powershell
uvx mpremote connect COM3 fs cp outputs/evt0-validation/ili9341.py :ili9341.py
uvx mpremote connect COM3 fs cp outputs/evt0-validation/ft6336.py :ft6336.py
uvx mpremote connect COM3 fs cp outputs/evt0-validation/lcd_test.py :lcd_test.py
uvx mpremote connect COM3 exec "import lcd_test"
```

Expected result:

1. A pale test page appears on the LCD.
2. The display prints `ILI9341 frame sent`.
3. The I2C scan prints the touch controller address.
4. Touching the panel prints `touch: [(x, y, strength)]` once the controller
   protocol matches.

The official module is documented at
<https://www.lcdwiki.com/zh/2.8inch_IPS_SPI_Module_ILI9341>. If the display
stays dark, first verify `5V`, `GND`, reset and backlight pins. Touch requires
the FT6336G to respond at `0x38`.

## Touchless UI validation

Display validation does not depend on touch. `ui_demo.py` automatically cycles
through a status page, target list and radar page, clearly marks all sample data
as simulated, and leaves the radar page visible:

```powershell
uvx mpremote connect COM3 fs cp outputs/evt0-validation/ui_demo.py :ui_demo.py
uvx mpremote connect COM3 exec "import ui_demo"
```

Touch bring-up is intentionally deferred until a controller responds at `0x38`
or `0x39`. It is not a blocker for display, protocol-decoder or replay tests.

### Repository pocket UI

`pocket_ui.py` implements the 240 x 320 visual scheme from the Git repository:

- deep green receiver background;
- compact RID status header;
- three-ring north-up radar;
- orange selected-target ray and marker;
- perspective ground plane and relative-height column;
- large distance and relative-height readings;
- persistent `演示` label.

The Chinese labels are rendered by a generated 1-bit subset of Noto Sans CJK
SC. No TTF is loaded at runtime. The generated glyph data is in `ui_font.py`;
the SIL OFL 1.1 license is in `NotoSansCJK-OFL-1.1.txt`.

```powershell
uvx mpremote connect COM3 fs cp outputs/evt0-validation/ui_font.py :ui_font.py
uvx mpremote connect COM3 fs cp outputs/evt0-validation/pocket_ui.py :pocket_ui.py
uvx mpremote connect COM3 exec "import pocket_ui"
```

The hardware run renders radar and height views from the decoded replay store,
including one selected target, another positioned target, and an identity-only
target that does not appear on the radar.

`main.py` makes the pocket UI persistent after board reset or USB reconnect:

```powershell
uvx mpremote connect COM3 fs cp outputs/evt0-validation/main.py :main.py
uvx mpremote connect COM3 reset
```

The display alternates radar and height after eight position updates
(approximately every 8 seconds). Send Ctrl-C over the MicroPython REPL to stop
the loop and access the filesystem.

The persistent build now animates a replay path around receiver-local
`(0, 0, 0)`:

- selected aircraft orbits at 168 m radius;
- altitude varies between approximately 44 and 80 m relative to the receiver;
- a second target moves independently;
- the identity-only target remains visible in the target count but never
  appears on the radar;
- radar and height views alternate automatically while the positions update.

Measured on the P4 with the current 240 x 320 SPI panel: software scene drawing
is about 113 ms and the SPI frame transfer is about 394 ms, so approximately
1 Hz animation is practical. The UI still displays `演示` because these points
are generated locally, not decoded from a live RF capture.

## RID decode and replay

The implemented validation path is:

```text
raw 802.11 Beacon / Probe Response
  -> vendor IE FA:0B:BC
  -> GB 46750-2025 or ASTM/OpenDroneID
  -> normalized observation
  -> target identity/position state
  -> list, detail and radar pages
```

`rid_decoder.py` currently decodes:

- GB 46750-2025 vendor type `0xF0`, flag fields 001-021;
- ASTM/OpenDroneID vendor type `0x0D` message packs;
- Basic ID, Location/Vector, Self ID, System and Operator ID messages;
- source MAC, RSSI and channel as receiver metadata.

`rid_state.py` keeps identity age and position age separate. Position goes
stale after 3 seconds and the target is removed from live views after 10
seconds. A target without a valid position never appears on the radar.

Run the host tests:

```powershell
Set-Location outputs/evt0-validation
py -m unittest -v test_rid_validation.py
```

Run the on-device decode/replay UI:

```powershell
uvx mpremote connect COM3 fs cp outputs/evt0-validation/rid_decoder.py :rid_decoder.py
uvx mpremote connect COM3 fs cp outputs/evt0-validation/rid_fixtures.py :rid_fixtures.py
uvx mpremote connect COM3 fs cp outputs/evt0-validation/rid_state.py :rid_state.py
uvx mpremote connect COM3 fs cp outputs/evt0-validation/rid_demo.py :rid_demo.py
uvx mpremote connect COM3 exec "import rid_demo"
```

The on-device demo decodes six generated beacon frames, renders two targets,
and exercises active, stale and expired states. Every page is marked
`REPLAY`/`GENERATED FIXTURE`; this is not a real RF reception claim.

For a real capture, provide one raw IEEE 802.11 frame per line as hex, or use
JSONL fields `frameHex`, `rssiDbm`, `channel` and `receivedMs`:

```powershell
py decode_capture.py capture.hex --channel 6
py decode_capture.py capture.jsonl
```

Output is NDJSON containing the normalized observation and current target
state. Invalid or unrecognized frames return a structured error.

For a controlled over-the-air source, [virtual_rid_tx.py](virtual_rid_tx.py)
generates GB 46750 and ASTM Beacon frames. It requires a Linux-supported
monitor/injection interface; the connected MT7612U is suitable under Linux,
while the stock Windows WLAN driver is not. See
[VIRTUAL_RID_SOURCE.md](VIRTUAL_RID_SOURCE.md).

## Current limits

- The decoder accepts IEEE 802.11 Beacon and Probe Response frames after the
  radio/radiotap wrapper has been removed.
- Wi-Fi 2.4/5.8 GHz capture, BLE and NAN are not yet connected on this
  MicroPython image.
- ASTM Authentication payloads are recognized but not cryptographically
  verified.
- A valid packet format does not prove identity authentication or precise
  position.
- GB 46750 and ASTM fixtures are deterministic protocol tests, not captured
  over-the-air evidence.
