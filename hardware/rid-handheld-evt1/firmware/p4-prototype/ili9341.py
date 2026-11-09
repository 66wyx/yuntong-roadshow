"""Minimal ILI9341 RGB565 driver for the EVT0 MicroPython validation rig."""

import framebuf
import machine
import time


def rgb565(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


class ILI9341:
    WIDTH = 240
    HEIGHT = 320

    def __init__(
        self,
        *,
        sck=26,
        mosi=23,
        miso=32,
        cs=20,
        dc=22,
        rst=21,
        bl=27,
        baudrate=20_000_000,
    ):
        self.cs = machine.Pin(cs, machine.Pin.OUT, value=1)
        self.dc = machine.Pin(dc, machine.Pin.OUT, value=1)
        self.rst = machine.Pin(rst, machine.Pin.OUT, value=1)
        self.bl = machine.Pin(bl, machine.Pin.OUT, value=0)
        self.spi = machine.SPI(
            1,
            baudrate=baudrate,
            polarity=0,
            phase=0,
            bits=8,
            firstbit=machine.SPI.MSB,
            sck=machine.Pin(sck),
            mosi=machine.Pin(mosi),
            miso=machine.Pin(miso),
        )
        self.width = self.WIDTH
        self.height = self.HEIGHT
        self._init()

    def _command(self, command, data=b""):
        self.cs(0)
        self.dc(0)
        self.spi.write(bytes((command,)))
        if data:
            self.dc(1)
            self.spi.write(data)
        self.cs(1)

    def _init(self):
        self.cs(0)
        self.rst(1)
        time.sleep_ms(50)
        self.rst(0)
        time.sleep_ms(100)
        self.rst(1)
        time.sleep_ms(50)

        self._command(0xCF, bytes((0x00, 0xC1, 0x30)))
        self._command(0xED, bytes((0x64, 0x03, 0x12, 0x81)))
        self._command(0xE8, bytes((0x85, 0x00, 0x78)))
        self._command(0xCB, bytes((0x39, 0x2C, 0x00, 0x34, 0x02)))
        self._command(0xF7, bytes((0x20,)))
        self._command(0xEA, bytes((0x00, 0x00)))
        self._command(0xC0, bytes((0x13,)))
        self._command(0xC1, bytes((0x13,)))
        self._command(0xC5, bytes((0x22, 0x35)))
        self._command(0xC7, bytes((0xBD,)))
        self._command(0x21)
        self._command(0x36, bytes((0x08,)))
        self._command(0xB6, bytes((0x0A, 0xA2)))
        self._command(0x3A, bytes((0x55,)))
        self._command(0xF6, bytes((0x01, 0x30)))
        self._command(0xB1, bytes((0x00, 0x1B)))
        self._command(0xF2, bytes((0x00,)))
        self._command(0x26, bytes((0x01,)))
        self._command(
            0xE0,
            bytes(
                (
                    0x0F,
                    0x35,
                    0x31,
                    0x0C,
                    0x0B,
                    0x0E,
                    0x06,
                    0x49,
                    0xA7,
                    0x33,
                    0x07,
                    0x0F,
                    0x03,
                    0x0C,
                    0x0A,
                    0x00,
                )
            ),
        )
        self._command(
            0xE1,
            bytes(
                (
                    0x00,
                    0x0E,
                    0x0A,
                    0x0F,
                    0x04,
                    0x11,
                    0x08,
                    0x36,
                    0x58,
                    0x4D,
                    0x07,
                    0x10,
                    0x0C,
                    0x32,
                    0x34,
                    0x0F,
                )
            ),
        )
        self._command(0x11)
        time.sleep_ms(120)
        self._command(0x29)
        self.bl(1)

    def _window(self, x, y, width, height):
        x1 = x + width - 1
        y1 = y + height - 1
        self._command(
            0x2A,
            bytes((x >> 8 & 0xFF, x & 0xFF, x1 >> 8 & 0xFF, x1 & 0xFF)),
        )
        self._command(
            0x2B,
            bytes((y >> 8 & 0xFF, y & 0xFF, y1 >> 8 & 0xFF, y1 & 0xFF)),
        )
        self._command(0x2C)

    def show(self, buffer):
        expected = self.width * self.height * 2
        if len(buffer) != expected:
            raise ValueError("expected %d-byte RGB565 frame" % expected)
        self._window(0, 0, self.width, self.height)
        self.cs(0)
        self.dc(1)
        swapped = bytearray(2048)
        view = memoryview(buffer)
        for start in range(0, len(buffer), 2048):
            chunk = view[start : start + 2048]
            count = len(chunk)
            usable = count & ~1
            for i in range(0, usable, 2):
                swapped[i] = chunk[i + 1]
                swapped[i + 1] = chunk[i]
            self.spi.write(memoryview(swapped)[:usable])
        self.cs(1)

    def new_frame(self):
        buffer = bytearray(self.width * self.height * 2)
        return buffer, framebuf.FrameBuffer(
            buffer, self.width, self.height, framebuf.RGB565
        )

