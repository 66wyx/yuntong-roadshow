"""List readable 8-bit register responses on the detected touch address."""

import machine


def probe():
    i2c = machine.I2C(0, scl=machine.Pin(8), sda=machine.Pin(7), freq=100_000)
    address = 0x18
    for register in range(256):
        try:
            i2c.writeto(address, bytes((register,)))
            value = i2c.readfrom(address, 4)
            if value != b"\xff\xff\xff\xff":
                print("%02x: %s" % (register, value.hex()))
        except OSError:
            pass
    print("register probe complete")


probe()
