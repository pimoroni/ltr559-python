#!/usr/bin/env python
import gpiod
from gpiod.line import Bias, Edge

from ltr559 import LTR559

print("""proximity-interrupt.py - Watch the LTR559 interrupt pin and trigger a function on change.

This script enables the LTR559's interrupt pin and sets up gpiod to watch it for changes.

Tap the LTR559 to trigger the interrupt.

Press Ctrl+C to exit!

""")


# /dev/gpiochip4 on a Raspberry Pi 5
GPIOCHIP = "/dev/gpiochip4"

# Breakout garden uses BCM4 as a shared interrupt pin
INTERRUPT_PIN = 4

# Below we're setting up the LTR559 INTERRUPT_PIN in active LOW mode
# This means it should be pulled "UP", which keeps it HIGH via a weak resistor
# and when the LTR559 asserts the interrupt pin it will pull i=t LOW giving
# us a "falling edge" transition to watch for.
request = gpiod.request_lines(
    GPIOCHIP,
    consumer="LTR559",
    config={
        INTERRUPT_PIN: gpiod.LineSettings(
            edge_detection=Edge.FALLING, bias=Bias.PULL_UP
        )
    },
)

# Enable interrupts and set the pin to active LOW mode
ltr559 = LTR559(enable_interrupts=True, interrupt_pin_polarity=0)

# Set the threshold outside which an interrupt will be triggered
ltr559.set_proximity_threshold(0, 1000)

# Tricky, since this value is *NOT* lux
# ltr559.set_light_threshold(20, 0xffff)


# This handler function is called by `add_event_detect` when a falling edge is detected on the INTERRUPT_PIN
def interrupt_handler(pin):
    int_als, int_ps = ltr559.get_interrupt()
    if int_ps or int_als:
        ltr559.update_sensor()
    if int_ps:
        print("Proximity interrupt: {}".format(ltr559.get_proximity()))
    # if int_als:
    #    print("Light sensor interrupt: {}".format(ltr559.get_lux()))


# Watch the INTERRUPT_PIN for a falling edge (HIGH/LOW transition)
while True:
    for event in request.read_edge_events():
        if event.line_offset == INTERRUPT_PIN:
            interrupt_handler(event.line_offset)
