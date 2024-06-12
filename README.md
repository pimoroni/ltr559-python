# LTR559 Proximity/Presence/Light Sensor

[![Build Status](https://img.shields.io/github/actions/workflow/status/pimoroni/ltr559-python/test.yml?branch=main)](https://github.com/pimoroni/ltr559-python/actions/workflows/test.yml)
[![Coverage Status](https://coveralls.io/repos/github/pimoroni/ltr559-python/badge.svg?branch=main)](https://coveralls.io/github/pimoroni/ltr559-python?branch=main)
[![PyPi Package](https://img.shields.io/pypi/v/ltr559.svg)](https://pypi.python.org/pypi/ltr559)
[![Python Versions](https://img.shields.io/pypi/pyversions/ltr559.svg)](https://pypi.python.org/pypi/ltr559)

Suitable for detecting proximity of an object at close range the LTR-559 is great for approach detection and ambient light compensation. The range is useful to around 5cm, and this is the type of sensor you might find in a smartphone to determine if you're holding it against your head.

### Full install (recommended):

We've created an easy installation script that will install all pre-requisites and get your LTR559
up and running with minimal efforts. To run it, fire up Terminal which you'll find in Menu -> Accessories -> Terminal
on your Raspberry Pi desktop, as illustrated below:

![Finding the terminal](http://get.pimoroni.com/resources/github-repo-terminal.png)

In the new terminal window type the command exactly as it appears below (check for typos) and follow the on-screen instructions:

```bash
git clone https://github.com/pimoroni/ltr559-python
cd ltr559-python
./install.sh
```

**Note** Libraries will be installed in the "pimoroni" virtual environment, you will need to activate it to run examples:

```
source ~/.virtualenvs/pimoroni/bin/activate
```

### Development:

If you want to contribute, or like living on the edge of your seat by having the latest code, you can install the development version like so:

```bash
git clone https://github.com/pimoroni/ltr559-python
cd ltr559-python
./install.sh --unstable
```