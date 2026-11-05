"""Detect which 8-bit registers change while the panel is touched."""

import machine
import time


def watch():
    i2c = machine.I2C(0, scl=machine.Pin(8), sda=machine.Pin(7), freq=100_000)
    previous = {}
    deadline = time.ticks_add(time.ticks_ms(), 30_000)
    while time.ticks_diff(deadline, time.ticks_ms()) > 0:
        for register in range(16):
            try:
                value = i2c.readfrom_mem(0x18, register, 1)[0]
                if previous.get(register) != value:
                    print("r%02x=%02x" % (register, value))
                    previous[register] = value
            except OSError:
                pass
        time.sleep_ms(30)
    print("8-bit touch watch complete")


watch()
