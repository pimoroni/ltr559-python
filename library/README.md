# LTR559 Proximity/Presence/Light Sensor

[![Build Status](https://travis-ci.com/pimoroni/ltr559-python.svg?branch=master)](https://travis-ci.com/pimoroni/ltr559-python)
[![Coverage Status](https://coveralls.io/repos/github/pimoroni/ltr559-python/badge.svg?branch=master)](https://coveralls.io/github/pimoroni/ltr559-python?branch=master)
[![PyPi Package](https://img.shields.io/pypi/v/ltr559.svg)](https://pypi.python.org/pypi/ltr559-python)
[![Python Versions](https://img.shields.io/pypi/pyversions/ltr559.svg)](https://pypi.python.org/pypi/ltr559-python)

Suitable for detecting proximity of an object at close range the LTR-559 is great for approach detection and ambient light compensation. The range is useful to around 5cm, and this is the type of sensor you might find in a smartphone to determine if you're holding it against your head.

# Installing

Stable library from PyPi:

* Just run `sudo pip3 install ltr559`

Latest/development library from GitHub:

* `git clone https://github.com/pimoroni/ltr559-python`
* `cd ltr559-python`
* `sudo ./install.sh`


0.1.0
-----

* Breaking API change to class for CircuitPython compatibility
* Port to new i2cdevice set/get API

0.0.4
-----

* Removed rogue print() of reset status

0.0.3
-----

* Fix PyPi readme formatting

0.0.2
-----

* Added default light-sensor options
* Fixed bugs & linted

0.0.1
-----

* Initial Release
