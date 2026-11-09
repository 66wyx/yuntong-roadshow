"""Find the actual SCL/SDA GPIO pair for an FT6336G connected to the P4."""

import machine
import time


PINS = (
    52,
    51,
    31,
    30,
    29,
    28,
    50,
    49,
    5,
    4,
    3,
    2,
    8,
    7,
    24,
    25,
    20,
    21,
    22,
    23,
    26,
    27,
    32,
    33,
    46,
    47,
    48,
)


def probe():
    valid = []
    for number in PINS:
        try:
            machine.Pin(number, machine.Pin.IN, machine.Pin.PULL_UP)
            valid.append(number)
        except ValueError:
            pass
    print("valid candidate pins:", valid)
    for scl in valid:
        for sda in valid:
            if scl == sda:
                continue
            bus = None
            try:
                bus = machine.SoftI2C(
                    scl=machine.Pin(scl, machine.Pin.PULL_UP),
                    sda=machine.Pin(sda, machine.Pin.PULL_UP),
                    freq=100_000,
                )
                bus.writeto(0x38, b"\x00")
                print("FT6336 candidate: SCL=GPIO%d SDA=GPIO%d" % (scl, sda))
            except OSError:
                pass
            finally:
                if bus is not None:
                    try:
                        bus.deinit()
                    except AttributeError:
                        pass
    print("touch pin scan complete")


probe()
