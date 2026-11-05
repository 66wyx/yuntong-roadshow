"""Identify externally pulled-up GPIOs without rewiring the hardware."""

import machine
import time

from find_touch import PINS


def probe():
    for number in PINS:
        try:
            pin = machine.Pin(number, machine.Pin.IN, machine.Pin.PULL_DOWN)
            time.sleep_ms(2)
            with_down = pin.value()
            pin.init(machine.Pin.IN, machine.Pin.PULL_UP)
            time.sleep_ms(2)
            with_up = pin.value()
            print(
                "GPIO%d pull-down=%d pull-up=%d%s"
                % (number, with_down, with_up, " EXTERNAL_PULLUP" if with_down else "")
            )
        except ValueError:
            pass


probe()
