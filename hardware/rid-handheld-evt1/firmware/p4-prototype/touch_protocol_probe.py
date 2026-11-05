"""Compare 8-bit and 16-bit register access using combined I2C transfers."""

import machine


def read(i2c, address, register_bytes, count):
    try:
        i2c.writeto(address, register_bytes, False)
        return bytes(i2c.readfrom(address, count))
    finally:
        i2c.stop()


def main():
    i2c = machine.I2C(0, scl=machine.Pin(8), sda=machine.Pin(7), freq=100_000)
    for address in (0x18, 0x1A):
        print("address", hex(address), "scan", i2c.scan())
        for register in (b"\x00", b"\x01", b"\x02", b"\x80", b"\xa0"):
            try:
                print(
                    "8-bit",
                    register.hex(),
                    read(i2c, address, register, 8).hex(),
                )
            except OSError as error:
                print("8-bit", register.hex(), error)
        for register in (b"\xd0\x05", b"\xd0\x00", b"\xd1\xf8", b"\xd2\x00"):
            try:
                print(
                    "16-bit",
                    register.hex(),
                    read(i2c, address, register, 8).hex(),
                )
            except OSError as error:
                print("16-bit", register.hex(), error)


main()
