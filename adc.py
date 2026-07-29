import machine
import time

# Pin 27 corresponds to ADC channel 1
adc = machine.ADC(28)

# Resistor values in Ohms
R1 = 10000.0
R2 = 2200.0

# Calculation multiplier derived from voltage divider: (R1 + R2) / R2
divider_ratio = (R1 + R2) / R2  # ~5.545

# Pico ADC reference voltage and resolution (16-bit in MicroPython: 0-65535)
REF_VOLTAGE = 3.3
ADC_MAX = 65535.0

while True:
    # Read raw 16-bit ADC value
    raw_value = adc.read_u16()
    
    # Calculate voltage at the ADC pin (0 - 3.3V)
    pin_voltage = (raw_value / ADC_MAX) * REF_VOLTAGE
    
    # Calculate actual battery voltage
    battery_voltage = pin_voltage * divider_ratio
    
    print(f"Raw: {raw_value} | ADC Pin: {pin_voltage:.2f}V | Battery: {battery_voltage:.1f}V")
    
    time.sleep(0.1)