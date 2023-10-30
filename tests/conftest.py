import sys
import mock
import pytest

from i2cdevice import MockSMBus


class _SMBusFakeDevice(MockSMBus):
    def __init__(self, i2c_bus):
        MockSMBus.__init__(self, i2c_bus)
        self.regs[0x86] = 0x09 << 4  # Fake part number
        self.regs[0x86] |= 0x02      # Fake revision
        self.regs[0x87] = 0x05       # Fake manufacturer ID

        self.regs[0x88:0x8C] = [0xff, 0xff, 0xff, 0xff]  # ALS CH0 & CH1

        self.regs[0x8C] = 0xff       # ALS / PS Status
        self.regs[0x8D] = 0xf0       # Proximity Data (240)


class _SMBusFakeDeviceNoTimeout(_SMBusFakeDevice):
    def __init__(self, i2c_bus):
        _SMBusFakeDevice.__init__(self, i2c_bus)

    def write_i2c_block_data(self, i2c_address, register, values):
        if register == 0x80:          # ALS_CONTROL
            values[0] &= ~0b00000010  # Mask out the soft reset bit
        return _SMBusFakeDevice.write_i2c_block_data(self, i2c_address, register, values)


@pytest.fixture(scope='function', autouse=False)
def GPIO():
    """Mock RPi.GPIO module."""
    GPIO = mock.MagicMock()
    # Fudge for Python < 37 (possibly earlier)
    sys.modules['RPi'] = mock.Mock()
    sys.modules['RPi'].GPIO = GPIO
    sys.modules['RPi.GPIO'] = GPIO
    yield GPIO
    del sys.modules['RPi']
    del sys.modules['RPi.GPIO']


@pytest.fixture(scope='function', autouse=False)
def smbus():
    """Mock smbus module."""
    smbus = mock.MagicMock()
    smbus.SMBus = _SMBusFakeDevice
    sys.modules['smbus'] = smbus
    yield smbus
    del sys.modules['smbus']


@pytest.fixture(scope='function', autouse=False)
def LTR559():
    from ltr559 import LTR559
    yield LTR559
    del sys.modules['ltr559']


@pytest.fixture(scope='function', autouse=False)
def SMBusFakeDevice():
    return _SMBusFakeDevice(1)


@pytest.fixture(scope='function', autouse=False)
def SMBusFakeDeviceNoTimeout():
    return _SMBusFakeDeviceNoTimeout(1)
