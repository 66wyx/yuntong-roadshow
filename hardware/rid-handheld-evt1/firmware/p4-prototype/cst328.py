"""Minimal CST328 touch reader for the EVT0 validation rig."""

import machine
import struct
import time


class CST328:
    ADDRESS = 0x1A
    POINT_COUNT = 0xD005
    POINT_DATA = 0xD000
    DEBUG_MODE = 0xD101
    NORMAL_MODE = 0xD109
    X_RES = 0xD1F8

    def __init__(self, *, scl=8, sda=7, rst=33, freq=100_000):
        self.reset = machine.Pin(rst, machine.Pin.OUT, value=1)
        self.i2c = machine.I2C(
            0, scl=machine.Pin(scl), sda=machine.Pin(sda), freq=freq
        )
        self.reset(1)
        time.sleep_ms(50)
        self.reset(0)
        time.sleep_ms(5)
        self.reset(1)
        time.sleep_ms(80)

    def scan(self):
        return self.i2c.scan()

    def _read(self, register, count):
        self.i2c.writeto(self.ADDRESS, struct.pack(">H", register))
        return self.i2c.readfrom(self.ADDRESS, count)

    def _write(self, register, data=b""):
        self.i2c.writeto(self.ADDRESS, struct.pack(">H", register) + data)

    def info(self):
        self._write(self.DEBUG_MODE)
        dimensions = self._read(self.X_RES, 4)
        self._write(self.NORMAL_MODE)
        return dimensions[1] << 8 | dimensions[0], dimensions[3] << 8 | dimensions[2]

    def read(self):
        count = self._read(self.POINT_COUNT, 1)[0] & 0x0F
        if not 1 <= count <= 5:
            self._write(self.POINT_COUNT, b"\x00")
            return []
        raw = self._read(self.POINT_DATA, 27)
        self._write(self.POINT_COUNT, b"\x00")
        points = []
        for i in range(count):
            offset = 1 if i == 0 else i * 5 + 3
            x = (raw[offset] << 4) | (raw[offset + 2] >> 4)
            y = (raw[offset + 1] << 4) | (raw[offset + 2] & 0x0F)
            strength = raw[offset + 3]
            points.append((x, y, strength))
        return points

