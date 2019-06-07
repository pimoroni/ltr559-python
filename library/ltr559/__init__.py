import time
from i2cdevice import Device, Register, BitField
from i2cdevice.adapter import Adapter, LookupAdapter, U16ByteSwapAdapter

__version__ = '0.0.4'

I2C_ADDR = 0x23

_is_setup = False
_als0 = 0
_als1 = 0
_ps0 = 0
_lux = 0

_ch0_c = (17743, 42785, 5926, 0)
_ch1_c = (-11059, 19548, -1185, 0)


class Bit12Adapter(Adapter):
    def _encode(self, value):
        """
        Convert the 16-bit output into the correct format for reading:

            0bLLLLLLLLXXXXHHHH -> 0bHHHHLLLLLLLL
        """
        return ((value & 0xFF)) << 8 | ((value & 0xF00) >> 8)

    def _decode(self, value):
        """
        Convert the 12-bit input into the correct format for the registers,
        the low byte followed by 4 empty bits and the high nibble:

            0bHHHHLLLLLLLL -> 0bLLLLLLLLXXXXHHHH
        """
        return ((value & 0xFF00) >> 8) | ((value & 0x000F) << 8)


_ltr559 = Device(I2C_ADDR, bit_width=8, registers=(
    Register('ALS_CONTROL', 0x80, fields=(
        BitField('gain', 0b00011100, adapter=LookupAdapter({
            1: 0b000,
            2: 0b001,
            4: 0b011,
            8: 0b011,
            48: 0b110,
            96: 0b111})),
        BitField('sw_reset', 0b00000010),
        BitField('mode', 0b00000001)
    )),

    Register('PS_CONTROL', 0x81, fields=(
        BitField('saturation_indicator_enable', 0b00100000),
        BitField('active', 0b00000011, adapter=LookupAdapter({
            False: 0b00,
            True: 0b11}))
    )),

    Register('PS_LED', 0x82, fields=(
        BitField('pulse_freq_khz', 0b11100000, adapter=LookupAdapter({
            30: 0b000,
            40: 0b001,
            50: 0b010,
            60: 0b011,
            70: 0b100,
            80: 0b101,
            90: 0b110,
            100: 0b111})),
        BitField('duty_cycle', 0b00011000, adapter=LookupAdapter({
            0.25: 0b00,
            0.5: 0b01,
            0.75: 0b10,
            1.0: 0b11})),
        BitField('current_ma', 0b00000111, adapter=LookupAdapter({
            5: 0b000,
            10: 0b001,
            20: 0b010,
            50: 0b011,
            100: 0b100}))
    )),

    Register('PS_N_PULSES', 0x83, fields=(
        BitField('count', 0b00001111),
    )),

    Register('PS_MEAS_RATE', 0x84, fields=(
        BitField('rate_ms', 0b00001111, adapter=LookupAdapter({
            10: 0b1000,
            50: 0b0000,
            70: 0b0001,
            100: 0b0010,
            200: 0b0011,
            500: 0b0100,
            1000: 0b0101,
            2000: 0b0110})),
    )),

    Register('ALS_MEAS_RATE', 0x85, fields=(
        BitField('integration_time_ms', 0b00111000, adapter=LookupAdapter({
            100: 0b000,
            50: 0b001,
            200: 0b010,
            400: 0b011,
            150: 0b100,
            250: 0b101,
            300: 0b110,
            350: 0b111})),
        BitField('repeat_rate_ms', 0b00000111, adapter=LookupAdapter({
            50: 0b000,
            100: 0b001,
            200: 0b010,
            500: 0b011,
            1000: 0b100,
            2000: 0b101}))
    )),

    Register('PART_ID', 0x86, fields=(
        BitField('part_number', 0b11110000),  # Should be 0x09H
        BitField('revision', 0b00001111)      # Should be 0x02H
    ), read_only=True, volatile=False),

    Register('MANUFACTURER_ID', 0x87, fields=(
        BitField('manufacturer_id', 0b11111111),  # Should be 0x05H
    ), read_only=True),

    # This will address 0x88, 0x89, 0x8A and 0x8B as a continuous 32bit register
    Register('ALS_DATA', 0x88, fields=(
        BitField('ch1', 0xFFFF0000, bit_width=16, adapter=U16ByteSwapAdapter()),
        BitField('ch0', 0x0000FFFF, bit_width=16, adapter=U16ByteSwapAdapter())
    ), read_only=True, bit_width=32),

    Register('ALS_PS_STATUS', 0x8C, fields=(
        BitField('als_data_valid', 0b10000000),
        BitField('als_gain', 0b01110000, adapter=LookupAdapter({
            1: 0b000,
            2: 0b001,
            4: 0b010,
            8: 0b011,
            48: 0b110,
            96: 0b111})),
        BitField('als_interrupt', 0b00001000),  # True = Interrupt is active
        BitField('als_data', 0b00000100),       # True = New data available
        BitField('ps_interrupt', 0b00000010),   # True = Interrupt is active
        BitField('ps_data', 0b00000001)         # True = New data available
    ), read_only=True),

    # The PS data is actually an 11bit value but since B3 is reserved it'll (probably) read as 0
    # We could mask the result if necessary
    Register('PS_DATA', 0x8D, fields=(
        BitField('ch0', 0xFF0F, adapter=Bit12Adapter()),
        BitField('saturation', 0x0080)
    ), bit_width=16, read_only=True),

    # INTERRUPT allows the interrupt pin and function behaviour to be configured.
    Register('INTERRUPT', 0x8F, fields=(
        BitField('polarity', 0b00000100),
        BitField('mode', 0b00000011, adapter=LookupAdapter({
            'off': 0b00,
            'ps': 0b01,
            'als': 0b10,
            'als+ps': 0b11}))
    )),

    Register('PS_THRESHOLD', 0x90, fields=(
        BitField('upper', 0xFF0F0000, adapter=Bit12Adapter(), bit_width=16),
        BitField('lower', 0x0000FF0F, adapter=Bit12Adapter(), bit_width=16)
    ), bit_width=32),

    # PS_OFFSET defines the measurement offset value to correct for proximity
    # offsets caused by device variations, crosstalk and other environmental factors.
    Register('PS_OFFSET', 0x94, fields=(
        BitField('offset', 0x03FF),  # Last two bits of 0x94, full 8 bits of 0x95
    ), bit_width=16),

    # Defines the upper and lower limits of the ALS reading.
    # An interrupt is triggered if values fall outside of this range.
    # See also INTERRUPT_PERSIST.
    Register('ALS_THRESHOLD', 0x97, fields=(
        BitField('upper', 0xFFFF0000, adapter=U16ByteSwapAdapter(), bit_width=16),
        BitField('lower', 0x0000FFFF, adapter=U16ByteSwapAdapter(), bit_width=16)
    ), bit_width=32),

    # This register controls how many values must fall outside of the range defined
    # by upper and lower threshold limits before the interrupt is asserted.

    # In the case of both PS and ALS, a 0 value indicates that every value outside
    # the threshold range should be counted.
    # Values therein map to n+1 , ie: 0b0001 requires two consecutive values.
    Register('INTERRUPT_PERSIST', 0x9E, fields=(
        BitField('PS', 0xF0),
        BitField('ALS', 0x0F)
    ))

))


def get_part_id():
    """Get part number"""
    setup()
    return _ltr559.PART_ID.get_part_number()


def get_revision():
    """Get revision ID"""
    setup()
    return _ltr559.PART_ID.get_revision()


def setup():
    """Set up the LTR559 sensor"""
    global _is_setup
    if _is_setup:
        return
    _is_setup = True

    with _ltr559.PART_ID as PART_ID:
        if PART_ID.get_part_number() != 0x09 or PART_ID.get_revision() != 0x02:
            raise RuntimeError("LTR559 not found")

    _ltr559.ALS_CONTROL.set_sw_reset(1)

    try:
        while True:
            status = _ltr559.ALS_CONTROL.get_sw_reset()
            # print("Status: {}".format(status))
            if status == 0:
                break
            time.sleep(0.05)

    except KeyboardInterrupt:
        pass

    with _ltr559.PS_LED as PS_LED:
        PS_LED.set_current_ma(50)
        PS_LED.set_duty_cycle(1.0)
        PS_LED.set_pulse_freq_khz(30)
        PS_LED.write()

    _ltr559.PS_N_PULSES.set_count(1)

    with _ltr559.ALS_CONTROL as ALS_CONTROL:
        ALS_CONTROL.set_mode(1)
        ALS_CONTROL.set_gain(4)
        ALS_CONTROL.write()

    with _ltr559.PS_CONTROL as PS_CONTROL:
        PS_CONTROL.set_active(True)
        PS_CONTROL.set_saturation_indicator_enable(1)
        PS_CONTROL.write()

    _ltr559.PS_MEAS_RATE.set_rate_ms(100)
    _ltr559.ALS_MEAS_RATE.set_integration_time_ms(50)
    _ltr559.ALS_MEAS_RATE.set_repeat_rate_ms(50)

    with _ltr559.ALS_THRESHOLD as ALS_THRESHOLD:
        ALS_THRESHOLD.set_lower(0x0000)
        ALS_THRESHOLD.set_upper(0xFFFF)
        ALS_THRESHOLD.write()

    with _ltr559.PS_THRESHOLD as PS_THRESHOLD:
        PS_THRESHOLD.set_lower(0b0000)
        PS_THRESHOLD.set_upper(0xFFFF)
        PS_THRESHOLD.write()

    _ltr559.PS_OFFSET.set_offset(0)

    _ltr559.INTERRUPT.set_mode('als+ps')


def set_light_threshold(lower, upper):
    """Set light interrupt threshold

    :param lower: Lower threshold
    :param upper: Upper threshold

    """
    setup()
    with _ltr559.ALS_THRESHOLD as ALS_THRESHOLD:
        ALS_THRESHOLD.set_lower(lower)
        ALS_THRESHOLD.set_upper(upper)
        ALS_THRESHOLD.write()


def set_proximity_threshold(lower, upper):
    """Set proximity interrupt threshold

    :param lower: Lower threshold
    :param upper: Upper threshold

    """
    setup()
    with _ltr559.PS_THRESHOLD as PS_THRESHOLD:
        PS_THRESHOLD.set_lower(lower)
        PS_THRESHOLD.set_upper(upper)


def set_proximity_rate_ms(rate_ms):
    """Set proximity measurement repeat rate in milliseconds

    :param rate_ms: Time in milliseconds- one of 10, 50, 70, 100, 200, 500, 1000 or 2000

    """
    setup()
    _ltr559.PS_MEAS_RATE.set_rate_ms(rate_ms)


def set_light_integration_time_ms(time_ms):
    """Set light integration time in milliseconds

    :param time_ms: Time in milliseconds- one of 50, 100, 150, 200, 300, 350, 400

    """
    setup()
    _ltr559.ALS_MEAS_RATE.set_integration_time_ms(time_ms)


def set_light_repeat_rate_ms(rate_ms):
    """Set light measurement repeat rate in milliseconds

    :param rate_ms: Rate in milliseconds- one of 50, 100, 200, 500, 1000 or 2000

    """
    setup()
    _ltr559.ALS_MEAS_RATE.set_repeat_rate_ms(rate_ms)


def set_interrupt_mode(enable_light=True, enable_proximity=True):
    """Set the intterupt mode

    :param enable_light: Enable the light sensor interrupt
    :param enable_proximity: Enable the proximity sensor interrupt

    """
    setup()
    mode = []

    if enable_light:
        mode.append('als')

    if enable_proximity:
        mode.append('ps')

    _ltr559.INTERRUPT.set_mode('+'.join(mode))


def set_proximity_active(active=True):
    """Enable/disable proximity sensor

    :param active: True for enabled, False for disabled

    """
    setup()
    _ltr559.PS_CONTROL.set_active(active)


def set_proximity_saturation_indictator(enabled=True):
    """Enable/disable the proximity saturation indicator

    :param enabled: True for enabled, False for disabled

    """
    setup()
    _ltr559.PS_CONTROL.set_saturation_indicator_enable(enabled)


def set_proximity_offset(offset):
    """Setup the proximity compensation offset

    :param offset: Offset value from 0 to 1023

    """
    setup()
    return _ltr559.PS_OFFSET.set_offset(offset)


def set_proximity_led(current_ma=50, duty_cycle=1.0, pulse_freq_khz=30, num_pulses=1):
    """Setup the proximity led current and properties

    :param current_ma: LED current in milliamps- one of 5, 10, 20, 50 or 100
    :param duty_cycle: LED duty cucle- one of 0.25, 0.5, 0.75 or 1.0 (25%, 50%, 75% or 100%)
    :param pulse_freq_khz: LED pulse frequency- one of 30, 40, 50, 60, 70, 80, 90 or 100
    :param num_pulse: Number of LED pulses to be emitted- 1 to 15

    """
    setup()
    with _ltr559.PS_LED as PS_LED:
        PS_LED.set_current_ma(current_ma)
        PS_LED.set_duty_cycle(duty_cycle)
        PS_LED.set_pulse_freq_khz(pulse_freq_khz)
        PS_LED.write()

    _ltr559.PS_N_PULSES.set_count(num_pulses)


def set_light_options(active=True, gain=4):
    """Set the mode and gain for the light sensor

    :param active: True for Active Mode, False for Stand-by Mode
    :param gain: Light sensor gain x- one of 1, 2, 4, 8, 48 or 96

    1x = 1 to 64k lux
    2x = 0.5 to 32k lux
    4x = 0.25 to 16k lux
    8x = 0.125 to 8k lux
    48x = 0.02 to 1.3k lux
    96x = 0.01 to 600 lux
    """
    setup()
    with _ltr559.ALS_CONTROL as ALS_CONTROL:
        ALS_CONTROL.set_mode(active)
        ALS_CONTROL.set_gain(gain)
        ALS_CONTROL.write()


def update_sensor():
    """Update the sensor lux and proximity values"""
    setup()
    global _ps0, _als0, _als1, _lux

    with _ltr559.ALS_PS_STATUS as ALS_PS_STATUS:
        ps_int = ALS_PS_STATUS.get_ps_interrupt() or ALS_PS_STATUS.get_ps_data()
        als_int = ALS_PS_STATUS.get_als_interrupt() or ALS_PS_STATUS.get_als_data()

    if ps_int:
        _ps0 = _ltr559.PS_DATA.get_ch0()

    if als_int:
        with _ltr559.ALS_DATA as ALS_DATA:
            _als0 = ALS_DATA.get_ch0()
            _als1 = ALS_DATA.get_ch1()

        ratio = 1000

        if _als0 + _als1 > 0:
            ratio = float(_als0 * 1000) / (_als1 + _als0)

        ch_idx = 3

        if ratio < 450:
            ch_idx = 0
        elif ratio < 640:
            ch_idx = 1
        elif ratio < 850:
            ch_idx = 2

        _lux = ((_als0 * _ch0_c[ch_idx]) - (_als1 * _ch1_c[ch_idx])) / 10000.0


def get_lux():
    """Return the ambient light value in lux"""
    update_sensor()
    return _lux


def get_proximity():
    """Return the proximity"""
    update_sensor()
    return _ps0


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
