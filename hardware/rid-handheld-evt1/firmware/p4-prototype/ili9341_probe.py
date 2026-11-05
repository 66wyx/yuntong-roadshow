"""Read the ILI9341 identification bytes over the selected SPI wiring."""

import machine
import time


def probe():
    cs = machine.Pin(20, machine.Pin.OUT, value=1)
    dc = machine.Pin(22, machine.Pin.OUT, value=1)
    rst = machine.Pin(21, machine.Pin.OUT, value=1)
    machine.Pin(27, machine.Pin.OUT, value=0)
    spi = machine.SPI(
        1,
        baudrate=4_000_000,
        polarity=0,
        phase=0,
        bits=8,
        firstbit=machine.SPI.MSB,
        sck=machine.Pin(26),
        mosi=machine.Pin(23),
        miso=machine.Pin(32),
    )
    rst(0)
    time.sleep_ms(50)
    rst(1)
    time.sleep_ms(120)
    for command in (0x04, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F):
        cs(0)
        dc(0)
        spi.write(bytes((command,)))
        dc(1)
        data = spi.read(4)
        cs(1)
        print("%02x: %s" % (command, data.hex()))


probe()
