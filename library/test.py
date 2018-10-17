import time
import ltr559 as l

assert l._ltr559.PART_ID.get_part_number() == 0x09
assert l._ltr559.PART_ID.get_revision() == 0x02

print("""
Found LTR-559.
Part ID: 0x{:02x}
Revision: 0x{:02x}
""".format(
    l._ltr559.PART_ID.get_part_number(),
    l._ltr559.PART_ID.get_revision())
)

print("""
Testing helper methods.        
""")
print(l._leading_zeros(0b00011111))
assert l._leading_zeros(0b00011111) == 3
assert l._trailing_zeros(0b00111100) == 2
assert l._leading_zeros(0b00111100) == 2

"""
l.ALS_CONTROL.set_gain(96)
assert l.ALS_CONTROL.get_gain() == 96
print(l.ALS_CONTROL.get_value())
assert l.ALS_CONTROL.get_value() == 0b111 << 2
assert repr(l.ALS_CONTROL) == "0b00011100"
print(l.ALS_CONTROL)

l.PS_N_PULSES.set_count(7)
assert l.PS_N_PULSES.get_count() == 7
assert l.PS_N_PULSES.get_value() == 0b111
print(l.PS_N_PULSES)
"""

print("""
Testing PS_THRESHOLD.set_lower
""")
tests = [0b110111011101, 0b111111111111]

for test in tests:
    print("{:012b}".format(test))
    l.PS_THRESHOLD.set_lower(test)
    print(l.PS_THRESHOLD)
    value = l.PS_THRESHOLD.get_lower()
    print("{:012b} == {:012b}".format(test, value))

print("""
Soft Reset
""")
l.ALS_CONTROL.set_sw_reset(1)
try:
    while True:
        status = l.ALS_CONTROL.get_sw_reset()
        print("Status: {}".format(status))
        if status == 0:
            break
        time.sleep(1.0)
except KeyboardInterrupt:
    pass


print("Setting ALS threshold")
l.ALS_THRESHOLD.set_lower(0x0000, False)
l.ALS_THRESHOLD.set_upper(0xFFFF, False)
l.ALS_THRESHOLD.write()

print("Setting PS threshold")
l.PS_THRESHOLD.set_lower(0,    False)
l.PS_THRESHOLD.set_upper(500, False)
l.PS_THRESHOLD.write()

print("Setting integration time and repeat rate")
l.PS_MEAS_RATE.set_rate_ms(100)
l.ALS_MEAS_RATE.set_integration_time_ms(50)
l.ALS_MEAS_RATE.set_repeat_rate_ms(50)

print("""
Activating sensor
""")

l.INTERRUPT.set_mode('als+ps')
l.PS_CONTROL.set_active(True)
l.PS_CONTROL.set_saturation_indicator_enable(1)

l.PS_LED.set_current_ma(50, False)
l.PS_LED.set_duty_cycle(1.0, False)
l.PS_LED.set_pulse_freq_khz(30, False)
l.PS_LED.write()

l.PS_N_PULSES.set_count(1)

l.ALS_CONTROL.set_mode(1)
l.ALS_CONTROL.set_gain(4)

l.PS_OFFSET.set_offset(69)

als0 = 0
als1 = 0
ps0 = 0
lux = 0

ch0_c = (17743, 42785, 5926, 0)
ch1_c = (-11059, 19548, -1185, 0)

try:
    while True:
        l.ALS_PS_STATUS.read()
        ps_int = l.ALS_PS_STATUS.get_ps_interrupt(False) or l.ALS_PS_STATUS.get_ps_data(False)
        als_int = l.ALS_PS_STATUS.get_als_interrupt(False) or l.ALS_PS_STATUS.get_als_data(False)
        #print("ALS_PS_STATUS: {}".format(l.ALS_PS_STATUS))

        if ps_int:
            ps0 = l.PS_DATA.get_ch0()

        if als_int:
            l.ALS_DATA.read()
            als0 = l.ALS_DATA.get_ch0(False)
            als1 = l.ALS_DATA.get_ch1(False)
            ratio = 1000
            if als0 + als0 > 0:
                ratio = (als0 * 1000) / (als1 + als0)
    
            ch_idx = 3
            if ratio < 450:
                ch_idx = 0
            elif ratio < 640:
                ch_idx = 1
            elif ratio < 850:
                ch_idx = 2
            
            lux = ((als0 * ch0_c[ch_idx]) - (als1 * ch1_c[ch_idx])) / 10000

        # Status should be 0 in bits 0 and 2 after reads have completed
        #l.ALS_PS_STATUS.read()
        #print("ALS_PS_STATUS: {}".format(l.ALS_PS_STATUS))

        print("Lux: {:06.2f}, Light CH0: {:04d}, Light CH1: {:04d}, Proximity: {:04d}  New Data LP: 0b{:01d}{:01d}".format(lux, als0, als1, ps0, als_int, ps_int))
        time.sleep(0.05)
except KeyboardInterrupt:
    pass
