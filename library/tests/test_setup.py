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


def test_setup_not_present():
    sys.modules['smbus'] = mock.MagicMock()
    from ltr559 import setup
    with pytest.raises(RuntimeError):
        setup()


def test_setup_mock_present():
    smbus = mock.Mock()
    smbus.SMBus = SMBusFakeDevice
    from ltr559 import setup
    setup()
