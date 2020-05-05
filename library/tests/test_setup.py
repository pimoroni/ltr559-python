import pytest


def test_setup_not_present(LTR559, smbus):
    with pytest.raises(RuntimeError):
        ltr559 = LTR559()
        del ltr559


def test_setup_mock_present(LTR559, SMBusFakeDevice):
    from ltr559 import LTR559
    with pytest.raises(RuntimeError) as e:
        ltr559 = LTR559(i2c_dev=SMBusFakeDevice, timeout=0.5)
        del ltr559
        assert "Timeout" in str(e.value)


def test_setup_mock_notimeout(LTR559, SMBusFakeDeviceNoTimeout):
    from ltr559 import LTR559
    ltr559 = LTR559(i2c_dev=SMBusFakeDeviceNoTimeout, timeout=0.5)
    del ltr559
