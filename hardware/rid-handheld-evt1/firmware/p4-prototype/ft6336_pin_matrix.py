"""Try the four plausible FT6336 SCL/SDA/reset/interrupt orientations."""

import machine
import time


def probe():
    combinations = (
        (8, 7, 46, 48),
        (8, 7, 48, 46),
        (7, 8, 46, 48),
        (7, 8, 48, 46),
    )
    for scl, sda, reset_pin, interrupt_pin in combinations:
        reset = machine.Pin(reset_pin, machine.Pin.OUT, value=1)
        machine.Pin(interrupt_pin, machine.Pin.IN, machine.Pin.PULL_UP)
        reset(0)
        time.sleep_ms(20)
        reset(1)
        time.sleep_ms(500)
        bus = machine.SoftI2C(
            scl=machine.Pin(scl, machine.Pin.PULL_UP),
            sda=machine.Pin(sda, machine.Pin.PULL_UP),
            freq=100_000,
        )
        try:
            bus.writeto(0x38, b"\xa8")
            identity = bus.readfrom(0x38, 1)
            print(
                "FOUND SCL=%d SDA=%d RST=%d INT=%d ID=%s"
                % (scl, sda, reset_pin, interrupt_pin, identity.hex())
            )
        except OSError:
            print(
                "no FT6336 SCL=%d SDA=%d RST=%d INT=%d"
                % (scl, sda, reset_pin, interrupt_pin)
            )
        try:
            bus.deinit()
        except AttributeError:
            pass


probe()
