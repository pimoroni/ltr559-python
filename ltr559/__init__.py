from .device import _mask_width, _byte_swap, _leading_zeros, _trailing_zeros, _unmask, _mask, Device, Register, BitField

ltr559 = Device(0x23, bitwidth=8)

ALS_CONTROL = Register(ltr559, 0x80, fields=(
    BitField('gain', 0b00011100, values_map={1: 0b000, 2: 0b001, 4: 0b011, 8:0b011, 48:0b110, 96:0b111}),
    BitField('sw_reset', 0b00000010),
    BitField('mode', 0b00000001)
))

PS_CONTROL = Register(ltr559, 0x81, fields=(
    BitField('saturation_indicator_enable', 0b00100000),
    BitField('active', 0b00000011, values_map={False: 0b00, True: 0b11})
))

PS_LED = Register(ltr559, 0x82, fields=(
    BitField('pulse_freq_khz', 0b11100000, values_map={30: 0b000, 40: 0b001, 50: 0b010, 60: 0b011, 70: 0b100, 80: 0b101, 90: 0b110, 100: 0b111}),
    BitField('duty_cycle', 0b00011000, values_map={0.25: 0b00, 0.5: 0b01, 0.75: 0b10, 1.0: 0b11}),
    BitField('current_ma', 0b00000111, values_map={5: 0b000, 10: 0b001, 20: 0b010, 50: 0b011, 100: 0b100})
))

PS_N_PULSES = Register(ltr559, 0x83, fields=(
    BitField('count', 0b00001111),   
))

PS_MEAS_RATE = Register(ltr559, 0x84, fields=(
    BitField('rate_ms', 0b00001111, values_map={10: 0b1000, 50: 0b0000, 70: 0b0001, 100: 0b0010, 200: 0b0011, 500: 0b0100, 1000: 0b0101, 2000: 0b0110}),    
))

ALS_MEAS_RATE = Register(ltr559, 0x85, fields=(
    BitField('integration_time_ms', 0b00111000, values_map={100: 0b000, 50: 0b001, 200: 0b010, 400: 0b011, 150: 0b100, 250: 0b101, 300: 0b110, 350: 0b111 }),
    BitField('repeat_rate_ms', 0b00000111, values_map={50: 0b000, 100: 0b001, 200: 0b010, 500: 0b011, 1000: 0b100, 2000: 0b101})
))

PART_ID = Register(ltr559, 0x86, fields=(
    BitField('part_number', 0b11110000), # Should be 0x09H
    BitField('revision', 0b00001111) # Should be 0x02H
), read_only=True, volatile=False)

MANUFACTURER_ID = Register(ltr559, 0x87, fields=(
    BitField('manufacturer_id', 0b11111111), # Should be 0x05H
), read_only=True)

# This will address 0x88, 0x89, 0x8A and 0x8B as a continuous 32bit register
ALS_DATA = Register(ltr559, 0x88, fields=(
    BitField('ch1', 0xFFFF0000, bitwidth=16, values_in=_byte_swap, values_out=_byte_swap),
    BitField('ch0', 0x0000FFFF, bitwidth=16, values_in=_byte_swap, values_out=_byte_swap)
), read_only=True, bitwidth=32)


ALS_PS_STATUS = Register(ltr559, 0x8C, fields=(
    BitField('als_data_valid', 0b10000000),
    BitField('als_gain', 0b01110000, values_map={1: 0b000, 2: 0b001, 4: 0b010, 8: 0b011, 48: 0b110, 96: 0b111}),
    BitField('als_interrupt', 0b00001000), # True = Interrupt is active
    BitField('als_data', 0b00000100), # True = New data available
    BitField('ps_interrupt', 0b00000010), # True = Interrupt is active
    BitField('ps_data', 0b00000001) # True = New data available
), read_only=True)

PS_DATA = Register(ltr559, 0x0D, fields=(
    BitField('ch0', 0xFFFF),
), bitwidth=16, read_only=True)

"""
INTERRUPT allows the interrupt pin and function behaviour to be configured.
"""
INTERRUPT = Register(ltr559, 0x8F, fields=(
    BitField('polarity', 0b00000100),
    BitField('mode', 0b00000011, values_map={'off': 0b00, 'ps': 0b01, 'als': 0b10, 'als+ps': 0b11})
))


"""
Convert the 16-bit output into the correct format for reading:

    0bLLLLLLLLXXXXHHHH -> 0bHHHHLLLLLLLL
"""
def map_threshold_out(value):
        return ((value & 0xFF00) >> 8) | ((value & 0x000F) << 8)

"""
Convert the 12-bit input into the correct format for the registers,
the low byte followed by 4 empty bits and the high nibble:

    0bHHHHLLLLLLLL -> 0bLLLLLLLLXXXXHHHH
"""
def map_threshold_in(value):
        return ((value & 0xFF) << 8) | ((value & 0xF00) >> 8)

PS_THRESHOLD = Register(ltr559, 0x90, fields=(
    BitField('upper', 0xFF0F0000, values_in=map_threshold_in, values_out=map_threshold_out),
    BitField('lower', 0x0000FF0F, values_in=map_threshold_in, values_out=map_threshold_out)
), bitwidth=32)


"""
PS_OFFSET defines the measurement offset value to correct for proximity
offsets caused by device variations, crosstalk and other environmental factors.
"""
PS_OFFSET = Register(ltr559, 0x94, fields=(
    BitField('offset', 0x03FF), # Last two bits of 0x94, full 8 bits of 0x95
))


"""
Defines the upper and lower limits of the ALS reading.
An interrupt is triggered if values fall outside of this range.
See also INTERRUPT_PERSIST.
"""
ALS_THRESHOLD = Register(ltr559, 0x97, fields=(
    BitField('upper', 0xFFFF0000, values_in=_byte_swap, values_out=_byte_swap),
    BitField('lower', 0x0000FFFF, values_in=_byte_swap, values_out=_byte_swap)
), bitwidth=32)

"""
This register controls how many values must fall outside of the range defined
by upper and lower threshold limits before the interrupt is asserted.

In the case of both PS and ALS, a 0 value indicates that every value outside
the threshold range should be counted.
Values therein map to n+1 , ie: 0b0001 requires two consecutive values.
"""
INTERRUPT_PERSIST = Register(ltr559, 0x9E, fields=(
    BitField('PS', 0xF0),
    BitField('ALS', 0x0F)
))


class REG:
    ALS_CONTR = 0x80 # ALS operation mode control SW reset, 0x00
    ALS_CONTR_GAIN_MASK = 0b00011100 
    ALS_CONTROL_GAIN_1X = 0b000  # 000 = 1x, 1 lux to 64k lux (default)
    ALS_CONTROL_GAIN_2X = 0b001  # 001 = 2x, 0.5 lux to 32k lux
    ALS_CONTROL_GAIN_4X = 0b010  # 010 = 4x, 0.25 lux to 16k lux
    ALS_CONTROL_GAIN_8X = 0b011  # 011 = 8x, 0.125 lux to 8k lux
                                 # 100 and 101 are reserved
    ALS_CONTROL_GAIN_48X = 0b110 # 110 = 48x, 0.02 lux to 1.3k lux
    ALS_CONTROL_GAIN_96X = 0b111 # 111 = 96x, 0.01 lux to 600 lux

    ALS_CONTR_SW_RESET_MASK = 0b00000010 # Initial start-up has: 0 = not started, 1 = started
    ALS_CONTR_ALS_MODE_MASK = 0b00000001 # 0 = Stand-by, 1 = Active
    ALS_CONTR_ALS_MODE_STANDBY = 0
    ALS_CONTR_ALS_MODE_ACTIVE = 1

    PS_CONTR = 0x81 # PS operation mode control, 0x00
    PS_CONTR_PS_SATURATION_INDICATOR_MASK = 0b00100000
    PS_CONTR_PS_MODE_MASK = 0b00000011 # 00 or 01 = Stand-by, 10 or 11 = Active

    PS_LED = 0x82 # PS LED setting, 0x7f
    N_PULSES = 0x83 # PS number of pulses, 0x01
    PS_MEAS_RATE = 0x84 # PS measurement rate in active mode, 0x02
    ALS_MEAS_RATE = 0x85 # ALS measurement rate in active mode, 0x03
    
    """
    These IDs should be checked at startup to ensure the correct
    sensor is present:
    * Part ID: 0x92
    * Manu ID: 0x05
    """
    PART_ID = 0x86 # Part Number ID and Revision ID, 0x92
    MANUFAC_ID = 0x87 # Manufacturer ID, 0x05

    """
    These registers should be read in sequence as a single block read
    When 0x8B (ALS_DATA_CH0_1) has been read, new data is populated
    """
    ALS_DATA_CH1_0 = 0x88 # ALS measurement CH1 data, lower byte, 0x00
    ALS_DATA_CH1_1 = 0x89 # ALS measurement CH1 data, upper byte, 0x00
    ALS_DATA_CH0_0 = 0x8A # ALS measurement CH0 data, lower byte, 0x00
    ALS_DATA_CH0_1 = 0x8B # ALS measurement CH0 data, upper byte, 0x00

    ALS_PS_STATUS = 0x8C # ALS and PS new data status, 0x00
    PS_DATA_0 = 0x8D # PS measurement data, lower byte, 0x00
    PS_DATA_1 = 0x8E # PS measurement data, upper byte, 0x00

    """
    The interrupt register should only be changed when the device is not active
    """
    INTERRUPT = 0x8F # Interrupt Settings

    PS_THRES_UP_0 = 0x90 # PS interrupt upper threshold, lower byte, 0xFF
    PS_THRES_UP_1 = 0x91 # PS interrupt upper threshold, upper byte, 0x07
    PS_THRES_LOW_0 = 0x92 # PS interrupt lower threshold, lower byte, 0x00
    PS_THRES_LOW_1 = 0x93 # PS interrupt lower threshold, upper byte, 0x00
    
    PS_OFFSET_1 = 0x94 # PS offset, upper byte, 0x00
    PS_OFFSET_0 = 0x95 # PS offset, lower byte, 0x00
    
    ALS_THRES_UP_0 = 0x97 # ALS interrupt upper threshold, lower byte, 0xFF
    ALS_THRES_UP_1 = 0x98 # ALS interrupt upper threshold, upper byte, 0xFF
    ALS_THRES_LOW_0 = 0x99 # ALS interrupt lower threshold, lower byte, 0x00
    ALS_THRES_LOW_1 = 0x9A # ALS interrupt lower threshold, upper byte, 0x00
    
    INTERRUPT_PERSIST = 0x95 # ALS / PS interrupt persist setting
