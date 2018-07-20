#!/bin/env python

from ltr559 import setup, update_sensor, get_lux, get_proximity

if __name__ == "__main__":
    setup()
    try:
        while True:
            update_sensor()
            lux = get_lux()
            prox = get_proximity()

            print("Lux: {:06.2f}, Proximity: {:04d}".format(lux, prox))

            time.sleep(0.05)
    except KeyboardInterrupt:
        pass
