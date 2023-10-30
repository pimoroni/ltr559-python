def test_get_proximity(LTR559, SMBusFakeDeviceNoTimeout):
    ltr559 = LTR559(i2c_dev=SMBusFakeDeviceNoTimeout, timeout=0.5)
    proximity = ltr559.get_proximity()
    assert proximity == 240


def test_get_lux(LTR559, SMBusFakeDeviceNoTimeout):
    ltr559 = LTR559(i2c_dev=SMBusFakeDeviceNoTimeout, timeout=0.5)
    lux = ltr559.get_lux()
    assert int(lux) == 76141


def test_set_light_integration_time_ms(LTR559, SMBusFakeDeviceNoTimeout):
    ltr559 = LTR559(i2c_dev=SMBusFakeDeviceNoTimeout, timeout=0.5)
    ltr559.set_light_integration_time_ms(150)
    assert SMBusFakeDeviceNoTimeout.regs[0x85] & 0b00111000 == 0b100 << 3


def test_set_interrupt_mode(LTR559, SMBusFakeDeviceNoTimeout):
    ltr559 = LTR559(i2c_dev=SMBusFakeDeviceNoTimeout, timeout=0.5)
    ltr559.set_interrupt_mode(enable_light=True, enable_proximity=True)
    assert SMBusFakeDeviceNoTimeout.regs[0x8F] & 0b11 == 0b11


def test_set_proximity_active(LTR559, SMBusFakeDeviceNoTimeout):
    ltr559 = LTR559(i2c_dev=SMBusFakeDeviceNoTimeout, timeout=0.5)
    ltr559.set_proximity_active(active=True)
    assert SMBusFakeDeviceNoTimeout.regs[0x81] & 0b11 == 0b11
