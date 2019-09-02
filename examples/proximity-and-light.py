#!/usr/bin/env python

import time
from ltr559 import LTR559

ltr559 = LTR559()

try:
    while True:
        lux = ltr559.get_lux()
        prox = ltr559.get_proximity()

        print("Lux: {:06.2f}, Proximity: {:04d}".format(lux, prox))

        time.sleep(0.05)
except KeyboardInterrupt:
    pass
