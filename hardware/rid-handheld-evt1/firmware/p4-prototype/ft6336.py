"""FT6336G touch driver for LCDWiki MSP2834 on MicroPython."""

import machine
import time


class FT6336:
    ADDRESS = 0x38
    DEVICE_MODE = 0x00
    TOUCH_COUNT = 0x02
    TOUCH_DATA = 0x03
    ID_FOCALTECH = 0xA8
    ID_CIPHER_MID = 0x9F
    ID_CIPHER_HIGH = 0xA3

    def __init__(self, *, scl=8, sda=7, rst=46, int_pin=48, freq=100_000):
        self.int = machine.Pin(int_pin, machine.Pin.IN)
        self.reset = machine.Pin(rst, machine.Pin.OUT, value=1)
        self.i2c = machine.I2C(
            0, scl=machine.Pin(scl), sda=machine.Pin(sda), freq=freq
        )
        self.reset(1)
        time.sleep_ms(20)
        self.reset(0)
        time.sleep_ms(20)
        self.reset(1)
        time.sleep_ms(500)

    def scan(self):
        return self.i2c.scan()

    def _read(self, register, count):
        self.i2c.writeto(self.ADDRESS, bytes((register,)))
        return self.i2c.readfrom(self.ADDRESS, count)

    def check_id(self):
        focaltech = self._read(self.ID_FOCALTECH, 1)[0]
        cipher = self._read(self.ID_CIPHER_MID, 2)
        high = self._read(self.ID_CIPHER_HIGH, 1)[0]
        return focaltech, bytes(cipher), high

    def read(self):
        count = self._read(self.TOUCH_COUNT, 1)[0] & 0x0F
        if count < 1 or count > 2:
            return []
        points = []
        for index in range(count):
            raw = self._read(self.TOUCH_DATA + index * 6, 4)
            x = ((raw[0] & 0x0F) << 8) | raw[1]
            y = ((raw[2] & 0x0F) << 8) | raw[3]
            points.append((x, y))
        return points

