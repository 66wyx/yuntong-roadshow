# C6 raw Wi-Fi additions

This project starts from the Espressif `esp-hosted` slave example and adds a
small custom-RPC side channel for the P4 receiver.

The reviewed additions are:

- `main/wifi_raw_msgs.h`: packed command/event definitions.
- `main/wifi_raw_slave.c`: promiscuous callback, channel/filter commands, and
  raw 802.11 transmit support.
- `main/wifi_raw_slave.h`: initialization API.
- `main/CMakeLists.txt`: compiles the new source file.
- `main/esp_hosted_coprocessor.c`: calls `wifi_raw_slave_init()` during startup.
- `sdkconfig.defaults` / `sdkconfig`: ESP32-C6 and SDIO configuration used on
  the tested board.

## Custom RPC IDs

| ID | Direction | Purpose |
|---|---|---|
| `0x0100` | P4 -> C6 | enable/disable promiscuous mode |
| `0x0101` | P4 -> C6 | set primary/secondary channel |
| `0x0102` | P4 -> C6 | set promiscuous filter mask |
| `0x0103` | P4 -> C6 | inject a raw 802.11 frame |
| `0x0180` | C6 -> P4 | command response |
| `0x0200` | C6 -> P4 | promiscuous frame event |

## Review focus

- Confirm that these custom message IDs cannot collide with other
  `esp-hosted` peer-data users.
- Review the allocation/free lifetime of a promiscuous event while it is queued
  through `esp_hosted_send_custom_data`.
- Check whether `rx_ctrl.dump_len` or `sig_len` is the correct captured length
  for every PHY mode on C6.
- Confirm channel changes are safe while the single C6 radio is promiscuous.
- The C6 starts Wi-Fi in station mode and disables power save; review the
  interaction with the existing `esp-hosted` Wi-Fi lifecycle.

The implementation has been exercised on real hardware: management frames
continued arriving over SDIO. No successful injected RID Beacon has yet been
observed because the PC-side MT7612U failed earlier during `mt76x2u` probe.
