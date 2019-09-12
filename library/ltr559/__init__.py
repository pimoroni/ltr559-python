import time
from i2cdevice import Device, Register, BitField
from i2cdevice.adapter import Adapter, LookupAdapter, U16ByteSwapAdapter

__version__ = '0.1.0'

I2C_ADDR = 0x23


class Bit12Adapter(Adapter):
    def _encode(self, value):
        """
        Convert the 12-bit input into the correct format for the registers,
        the low byte followed by 4 empty bits and the high nibble:

            0bHHHHLLLLLLLL -> 0bLLLLLLLLXXXXHHHH
        """
        return ((value & 0xFF) << 8) | ((value & 0xF00) >> 8)

    def _decode(self, value):
        """
        Convert the 16-bit output into the correct format for reading:

            0bLLLLLLLLXXXXHHHH -> 0bHHHHLLLLLLLL
        """
        return ((value & 0xFF00) >> 8) | ((value & 0x000F) << 8)


class LTR559:
    def __init__(self, i2c_dev=None, enable_interrupts=False, interrupt_pin_polarity=1, timeout=5.0):
        self._als0 = 0
        self._als1 = 0
        self._ps0 = 0
        self._lux = 0
        self._gain = 4
        self._ratio = 100

        # Non default
        self._integration_time = 50

        self._ch0_c = (17743, 42785, 5926, 0)
        self._ch1_c = (-11059, 19548, -1185, 0)

        self._ltr559 = Device(I2C_ADDR, i2c_dev=i2c_dev, bit_width=8, registers=(
            Register('ALS_CONTROL', 0x80, fields=(
                BitField('gain', 0b00011100, adapter=LookupAdapter({
                    1: 0b000,
                    2: 0b001,
                    4: 0b010,
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
                BitField('upper', 0xFF0F0000, adapter=Bit12Adapter()),
                BitField('lower', 0x0000FF0F, adapter=Bit12Adapter())
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

        """Set up the LTR559 sensor"""
        self.part_id = self._ltr559.get('PART_ID')
        if self.part_id.part_number != 0x09 or self.part_id.revision != 0x02:
            raise RuntimeError("LTR559 not found")

        self._ltr559.set('ALS_CONTROL', sw_reset=1)

        t_start = time.time()
        while time.time() - t_start < timeout:
            status = self._ltr559.get('ALS_CONTROL').sw_reset
            if status == 0:
                break
            time.sleep(0.05)

        if self._ltr559.get('ALS_CONTROL').sw_reset:
            raise RuntimeError("Timeout waiting for software reset.")

        if enable_interrupts:
            self._ltr559.set('INTERRUPT',
                             mode='als+ps',
                             polarity=interrupt_pin_polarity)

        # FIXME use datasheet defaults or document
        self._ltr559.set('PS_LED',
                         current_ma=50,
                         duty_cycle=1.0,
                         pulse_freq_khz=30)

        self._ltr559.set('PS_N_PULSES', count=1)

        self._ltr559.set('ALS_CONTROL',
                         mode=1,
                         gain=self._gain)

        self._ltr559.set('PS_CONTROL',
                         active=True,
                         saturation_indicator_enable=1)

        self._ltr559.set('PS_MEAS_RATE', rate_ms=100)

        self._ltr559.set('ALS_MEAS_RATE',
                         integration_time_ms=self._integration_time,
                         repeat_rate_ms=50)

        self._ltr559.set('ALS_THRESHOLD',
                         lower=0x0000,
                         upper=0xFFFF)

        self._ltr559.set('PS_THRESHOLD',
                         lower=0x0000,
                         upper=0xFFFF)

        self._ltr559.set('PS_OFFSET', offset=0)

    def get_part_id(self):
        """Get part number"""
        return self.part_id.part_number

    def get_revision(self):
        """Get revision ID"""
        return self.part_id.revision

    def set_light_threshold(self, lower, upper):
        """Set light interrupt threshold

        :param lower: Lower threshold
        :param upper: Upper threshold

        """
        self._ltr559.set('ALS_THRESHOLD',
                         lower=lower,
                         upper=upper)

    def set_proximity_threshold(self, lower, upper):
        """Set proximity interrupt threshold

        :param lower: Lower threshold
        :param upper: Upper threshold

        """
        self._ltr559.set('PS_THRESHOLD',
                         lower=lower,
                         upper=upper)

    def set_proximity_rate_ms(self, rate_ms):
        """Set proximity measurement repeat rate in milliseconds

        :param rate_ms: Time in milliseconds- one of 10, 50, 70, 100, 200, 500, 1000 or 2000

        """
        self._ltr559.set('PS_MEAS_RATE', rate_ms)

    def set_light_integration_time_ms(self, time_ms):
        """Set light integration time in milliseconds

        :param time_ms: Time in milliseconds- one of 50, 100, 150, 200, 300, 350, 400

        """
        self._integration_time = time_ms
        self._ltr559.set('ALS_MEAS_RATE', integration_time_ms=time_ms)

    def set_light_repeat_rate_ms(self, rate_ms=100):
        """Set light measurement repeat rate in milliseconds

        :param rate_ms: Rate in milliseconds- one of 50, 100, 200, 500, 1000 or 2000

        """
        self._ltr559.set('ALS_MEAS_RATE', set_repeat_rate_ms=rate_ms)

    def set_interrupt_mode(self, enable_light=True, enable_proximity=True):
        """Set the intterupt mode

        :param enable_light: Enable the light sensor interrupt
        :param enable_proximity: Enable the proximity sensor interrupt

        """
        mode = []

        if enable_light:
            mode.append('als')

        if enable_proximity:
            mode.append('ps')

        self._ltr559.set('INTERRUPT', mode='+'.join(mode))

    def set_proximity_active(self, active=True):
        """Enable/disable proximity sensor

        :param active: True for enabled, False for disabled

        """
        self._ltr559.set('PS_CONTROL', set_active=active)

    def set_proximity_saturation_indictator(self, enabled=True):
        """Enable/disable the proximity saturation indicator

        :param enabled: True for enabled, False for disabled

        """
        self._ltr559.set('PS_CONTROL', saturation_indicator_enable=enabled)

    def set_proximity_offset(self, offset):
        """Setup the proximity compensation offset

        :param offset: Offset value from 0 to 1023

        """
        return self._ltr559.set('PS_OFFSET', offset=offset)

    def set_proximity_led(self, current_ma=50, duty_cycle=1.0, pulse_freq_khz=30, num_pulses=1):
        """Setup the proximity led current and properties

        :param current_ma: LED current in milliamps- one of 5, 10, 20, 50 or 100
        :param duty_cycle: LED duty cucle- one of 0.25, 0.5, 0.75 or 1.0 (25%, 50%, 75% or 100%)
        :param pulse_freq_khz: LED pulse frequency- one of 30, 40, 50, 60, 70, 80, 90 or 100
        :param num_pulse: Number of LED pulses to be emitted- 1 to 15

        """
        self._ltr559.set('PS_LED',
                         current_ma=current_ma,
                         duty_cycle=duty_cycle,
                         set_pulse_freq_khz=pulse_freq_khz)

        self._ltr559.set('PS_N_PULSES', num_pulses)

    def set_light_options(self, active=True, gain=4):
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
        self._gain = gain
        self._ltr559.set('ALS_CONTROL',
                         mode=active,
                         gain=gain)

    def update_sensor(self):
        """Update the sensor lux and proximity values"""
        status = self._ltr559.get('ALS_PS_STATUS')
        ps_int = status.ps_interrupt or status.ps_data
        als_int = status.als_interrupt or status.als_data

        if ps_int:
            self._ps0 = self._ltr559.get('PS_DATA').ch0

        if als_int:
            als = self._ltr559.get('ALS_DATA')
            self._als0 = als.ch0
            self._als1 = als.ch1

            self._ratio = self._als1 * 100 / (self._als1 + self._als0) if self._als0 + self._als1 > 0 else 101

            if self._ratio < 45:
                ch_idx = 0
            elif self._ratio < 64:
                ch_idx = 1
            elif self._ratio < 85:
                ch_idx = 2
            else:
                ch_idx = 3

            try:
                self._lux = (self._als0 * self._ch0_c[ch_idx]) - (self._als1 * self._ch1_c[ch_idx])
                self._lux /= (self._integration_time / 100.0)
                self._lux /= self._gain
                self._lux /= 10000.0
            except ZeroDivisionError:
                self._lux = 0

    def get_gain(self):
        """ Return gain used in lux calculation"""
        return self._gain

    def get_integration_time(self):
        """ Return integration time used in lux calculation"""
        return self._integration_time

    get_intt = get_integration_time

    def get_raw_als(self, passive=True):
        """ reurtn raw ALS channel data ch0,ch1 """
        if not passive:
            self.update_sensor()
        return self._als0, self._als1

    def get_ratio(self, passive=True):
        """Return the ambient light ratio between ALS channels"""
        if not passive:
            self.update_sensor()
        return self._ratio

    def get_lux(self, passive=False):
        """Return the ambient light value in lux"""
        if not passive:
            self.update_sensor()
        return self._lux

    def get_interrupt(self):
        """Return the light and proximity sensor interrupt status"""
        interrupt = self._ltr559.get('ALS_PS_STATUS')
        return interrupt.als_interrupt, interrupt.ps_interrupt

    def get_proximity(self, passive=False):
        """Return the proximity"""
        if not passive:
            self.update_sensor()
        return self._ps0


if __name__ == "__main__":
    import sys
    delay = float(sys.argv[1]) if len(sys.argv) == 2 and sys.argv[1].isnumeric() else 0.05
    ltr559 = LTR559()
    try:
        while True:
            ltr559.update_sensor()
            lux = ltr559.get_lux(passive=True)
            prox = ltr559.get_proximity(passive=True)

            print("Lux: {:07.2f}, Proximity: {:04d}".format(lux, prox))
            time.sleep(delay)
    except KeyboardInterrupt:
        pass
