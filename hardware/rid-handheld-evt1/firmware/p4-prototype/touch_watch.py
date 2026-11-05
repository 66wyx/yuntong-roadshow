"""Watch raw touch-controller responses without applying a vendor parser."""

import time

from cst328 import CST328


def watch():
    CST328.ADDRESS = 0x18
    touch = CST328()
    previous = None
    deadline = time.ticks_add(time.ticks_ms(), 20_000)
    while time.ticks_diff(deadline, time.ticks_ms()) > 0:
        try:
            count = touch._read(CST328.POINT_COUNT, 1)
            data = touch._read(CST328.POINT_DATA, 15)
            current = bytes(count + data)
            if current != previous:
                print("raw:", current.hex())
                previous = current
        except OSError as error:
            print("touch read error:", error)
            time.sleep_ms(250)
        time.sleep_ms(50)
    print("touch watch complete")


watch()
