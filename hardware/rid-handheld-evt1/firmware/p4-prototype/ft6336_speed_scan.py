"""Scan FT6336 at several I2C speeds on GPIO8/GPIO7."""

import machine
import time


def probe():
    reset = machine.Pin(46, machine.Pin.OUT, value=1)
    machine.Pin(48, machine.Pin.IN, machine.Pin.PULL_UP)
    reset(0)
    time.sleep_ms(20)
    reset(1)
    time.sleep_ms(500)
    for frequency in (10_000, 25_000, 50_000, 100_000, 200_000, 400_000):
        bus = machine.SoftI2C(
            scl=machine.Pin(8, machine.Pin.PULL_UP),
            sda=machine.Pin(7, machine.Pin.PULL_UP),
            freq=frequency,
        )
        try:
            found = bus.scan()
            print(frequency, [hex(address) for address in found])
        except OSError as error:
            print(frequency, "error", error)
        try:
            bus.deinit()
        except AttributeError:
            pass


probe()
