#!/usr/bin/env python
from ltr559 import LTR559
import signal
import RPi.GPIO as GPIO

print("""proximity-interrupt.py - Watch the LTR559 interrupt pin and trigger a function on change.

This script enables the LTR559's interrupt pin and sets up RPi.GPIO to watch it for changes.

Tap the LTR559 to trigger the interrupt.

Press Ctrl+C to exit!

""")


# Breakout garden uses BCM4 as a shared interrupt pin
INTERRUPT_PIN = 4

# Tell RPi.GPIO we'll be working with BCM pin numbering
GPIO.setmode(GPIO.BCM)

# Below we're setting up the LTR559 INTERRUPT_PIN in active LOW mode
# This means it should be pulled "UP", which keeps it HIGH via a weak resistor
# and when the LTR559 asserts the interrupt pin it will pull i=t LOW giving
# us a "falling edge" transition to watch for.
GPIO.setup(INTERRUPT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Enable interrupts and set the pin to active LOW mode
ltr559 = LTR559(enable_interrupts=True, interrupt_pin_polarity=0)

# Set the threshold outside which an interrupt will be triggered
ltr559.set_proximity_threshold(0, 1000)

# Tricky, since this value is *NOT* lux
# ltr559.set_light_threshold(20, 0xffff)


# This handler function is called by `add_event_detect` when a falling edge is detected on the INTERRUPT_PIN
def interrupt_handler(pin):
    int_als, int_ps = ltr559.get_interrupt()
    if int_ps:
        print("Proximity interrupt: {}".format(ltr559.get_proximity()))
    # if int_als:
    #    print("Light sensor interrupt: {}".format(ltr559.get_lux()))


# Watch the INTERRUPT_PIN for a falling edge (HIGH/LOW transition)
GPIO.add_event_detect(INTERRUPT_PIN, callback=interrupt_handler, edge=GPIO.FALLING)

# Prevent out Python script from exiting abruptly
signal.pause()
