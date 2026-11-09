"""Release the touch reset and locate the FT6336G without rewiring."""

import machine
import time

from find_touch import PINS


def candidate_pins():
    valid = []
    for number in PINS:
        try:
            machine.Pin(number, machine.Pin.IN, machine.Pin.PULL_UP)
            valid.append(number)
        except ValueError:
            pass
    return valid


def probe():
    pins = []
    for number in candidate_pins():
        pin = machine.Pin(number, machine.Pin.OUT)
        pin(0)
        pins.append((number, pin))
    time.sleep_ms(30)
    for _, pin in pins:
        pin(1)
    time.sleep_ms(500)

    found = []
    numbers = [number for number, _ in pins]
    for scl in numbers:
        for sda in numbers:
            if scl == sda:
                continue
            bus = None
            try:
                bus = machine.SoftI2C(
                    scl=machine.Pin(scl, machine.Pin.PULL_UP),
                    sda=machine.Pin(sda, machine.Pin.PULL_UP),
                    freq=100_000,
                )
                for address in (0x38, 0x39):
                    try:
                        bus.writeto(address, b"\x00")
                        found.append((scl, sda, address))
                    except OSError:
                        pass
            except OSError:
                pass
            finally:
                if bus is not None:
                    try:
                        bus.deinit()
                    except AttributeError:
                        pass
    print("FT6336 pin pairs:", found)


probe()
