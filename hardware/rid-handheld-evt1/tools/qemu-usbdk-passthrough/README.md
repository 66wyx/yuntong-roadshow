# QEMU UsbDk passthrough workaround

This directory contains the source used while diagnosing a Windows 11 USB
passthrough problem with the MT7612U (`0e8d:7612`).

QEMU's `usb-host` device uses libusb's WinUSB backend by default. UsbDk must
also be selected explicitly with `LIBUSB_OPTION_USE_USBDK`. The Windows QEMU
build used here does not make that selection on its own.

`usbdk_proxy.c` is an ABI-compatible `libusb-1.0.dll` proxy:

1. Forward ordinary libusb calls to the renamed original DLL.
2. Select the UsbDk backend after `libusb_init`.
3. Execute submitted control transfers synchronously on a worker thread.
4. Deliver their completion callbacks from QEMU's
   `libusb_handle_events_timeout` call, preserving QEMU's expected callback
   thread.
5. Add a settle delay after a physical reset.

`usbdk_probe.c` is a read-only host probe. It opens `0e8d:7612`, resets it,
claims interface 0, and reads the 4-byte value at register `0x09a8` using the
same vendor request as `mt76x2u`.

## Build with MinGW-w64

```bash
x86_64-w64-mingw32-gcc -shared -O2 usbdk_proxy.c \
  -Wl,usbdk_proxy.def -o libusb-1.0.dll
x86_64-w64-mingw32-gcc -O2 usbdk_probe.c -o usbdk_probe.exe
```

The original `libusb-1.0.dll` must be renamed `libusb_original.dll`. Run QEMU
from a directory containing the proxy and original DLL, with the normal QEMU
directory on `PATH`.

## Status

The host probe succeeds:

```text
open=0
reset_device=0
claim_interface_0=0
read_09a8=4 data=01000000
```

QEMU can enumerate the real device, but the Linux guest's `mt76x2u` driver
still reports:

```text
mt76x2u 1-1:1.0: vendor request req:07 off:09a8 failed:-110
```

Therefore this workaround is not yet a valid end-to-end transmitter solution.
It is committed for review because it isolates the failure to QEMU/UsbDk
control-transfer behavior rather than the card's basic USB response.

Do not commit QEMU executables, VM disks, or built DLL/EXE artifacts.
