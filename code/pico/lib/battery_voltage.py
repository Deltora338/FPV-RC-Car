"""This module's purpose is to read the battery's voltage.
The read() function is called in main.py to update the current battery voltage
which allows the computer and user to make decision about operations
"""
from machine import ADC

adc = ADC(28)

# Resistor values in Ohms
R1 = 10_000
R2 = 2_200

# voltage divider eqn: vin * (r2 / (r2 + r1))
# therefore inverse is v_read * (r2 + r1) / r2

divider_ratio = (R1 + R2) / R2  # approx 5.545 ratio

REF_VOLTAGE = 3.3
ADC_MAX = 65535


def read() -> float:
    total = 0
    for _ in range(10):
        total += adc.read_u16()
    
    reading = total // 10
    
    # voltage at pin 28
    pin_voltage = (reading / ADC_MAX) * REF_VOLTAGE
    
    # pin voltage converted back to the correlated battery voltage
    battery_voltage = pin_voltage * divider_ratio
    
    return battery_voltage
