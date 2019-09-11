import sys
import mock
import pytest
from i2cdevice import MockSMBus


class SMBusFakeDevice(MockSMBus):
    def __init__(self, i2c_bus):
        MockSMBus.__init__(self, i2c_bus)
        self.regs[0x86] = 0x09 << 4  # Fake part number
        self.regs[0x86] |= 0x02      # Fake revision
        self.regs[0x87] = 0x05       # Fake manufacturer ID


class SMBusFakeDeviceNoTimeout(SMBusFakeDevice):
    def __init__(self, i2c_bus):
        SMBusFakeDevice.__init__(self, i2c_bus)

    def write_i2c_block_data(self, i2c_address, register, values):
        if register == 0x80:          # ALS_CONTROL
            values[0] &= ~0b00000010  # Mask out the soft reset bit
        return SMBusFakeDevice.write_i2c_block_data(self, i2c_address, register, values)


def test_setup_not_present():
    sys.modules['smbus'] = mock.MagicMock()
    from ltr559 import LTR559
    with pytest.raises(RuntimeError):
        ltr559 = LTR559()
        del ltr559


def test_setup_mock_present():
    from ltr559 import LTR559
    with pytest.raises(RuntimeError) as e:
        ltr559 = LTR559(i2c_dev=SMBusFakeDevice(1), timeout=0.5)
        del ltr559
        assert "Timeout" in str(e.value)


def test_setup_mock_notimeout():
    from ltr559 import LTR559
    ltr559 = LTR559(i2c_dev=SMBusFakeDeviceNoTimeout(1), timeout=0.5)
    del ltr559
