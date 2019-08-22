#!/usr/bin/env python
import ltr559
import signal
import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setup(4, GPIO.IN, pull_up_down=GPIO.PUD_UP)

ltr559.set_proximity_threshold(0, 1000)

# Tricky, since this value is *NOT* lux
# ltr559.set_light_threshold(20, 0xffff)

def interrupt_handler(pin):
    int_als, int_ps = ltr559.get_interrupt()
    if int_ps:
        print("Proximity interrupt: {}".format(ltr559.get_proximity()))
    # if int_als:
    #    print("Light sensor interrupt: {}".format(ltr559.get_lux()))

GPIO.add_event_detect(4, callback=interrupt_handler, edge=GPIO.FALLING)

signal.pause()

