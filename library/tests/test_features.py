def test_get_proximity(LTR559, SMBusFakeDeviceNoTimeout):
    ltr559 = LTR559(i2c_dev=SMBusFakeDeviceNoTimeout, timeout=0.5)
    proximity = ltr559.get_proximity()
    assert proximity == 240


def test_get_lux(LTR559, SMBusFakeDeviceNoTimeout):
    ltr559 = LTR559(i2c_dev=SMBusFakeDeviceNoTimeout, timeout=0.5)
    lux = ltr559.get_lux()
    assert int(lux) == 76141
