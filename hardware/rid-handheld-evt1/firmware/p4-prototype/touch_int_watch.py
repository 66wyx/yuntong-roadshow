"""Watch the FT6336G interrupt pin after releasing its reset."""

import machine
import time


def watch():
    reset = machine.Pin(46, machine.Pin.OUT, value=1)
    time.sleep_ms(20)
    reset(0)
    time.sleep_ms(20)
    reset(1)
    time.sleep_ms(500)

    interrupt = machine.Pin(48, machine.Pin.IN, machine.Pin.PULL_UP)
    previous = interrupt.value()
    changes = 0
    low_samples = 0
    total_samples = 0
    deadline = time.ticks_add(time.ticks_ms(), 15_000)
    while time.ticks_diff(deadline, time.ticks_ms()) > 0:
        value = interrupt.value()
        total_samples += 1
        if value == 0:
            low_samples += 1
        if value != previous:
            changes += 1
            print("CTP_INT ->", value)
            previous = value
        time.sleep_ms(10)
    print(
        "CTP_INT changes=%d low_samples=%d/%d"
        % (changes, low_samples, total_samples)
    )


watch()
