# ESP32-C6 SDIO OTA flasher

This ESP32-P4 application pushes the embedded C6 slave image to the companion
ESP32-C6 over SDIO using `esp_hosted_slave_ota_*`.

`main/network_adapter.bin` is the C6 image produced from [`../c6`](../c6). It is
checked in because this OTA flasher cannot build without the exact image it
embeds. The C6 source remains authoritative; rebuild the binary after changing
the slave firmware.

## Build

```bash
idf.py set-target esp32p4
idf.py build
idf.py -p /dev/ttyACM0 flash monitor
```

The process reports the old C6 version, OTA progress, finalization, firmware
activation, and the version read back after reboot.

## Evidence

The OTA path completed on the real P4/C6 board and the custom C6 firmware
subsequently produced promiscuous packet events on the P4. This confirms the
SDIO OTA and custom RPC path is live, not replayed.
