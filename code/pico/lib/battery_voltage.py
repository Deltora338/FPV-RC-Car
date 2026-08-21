"""This module's purpose is to read the battery's voltage.
The read() function is called in main.py to update the current battery voltage
which allows the computer and user to make decision about operations
"""
from machine import ADC
import time

adc = ADC(28)

def read_battery_voltage(adc_pin) -> float:
    total = 0
    for _ in range(10):
        total += adc_pin.read_u16()
    
    reading = total // 10
    
    # voltage at adc_pin
    pin_voltage = (reading / 65535) * 3.3
    
    # pin voltage converted back to the correlated battery voltage
    battery_voltage = pin_voltage * ((10000 + 2000) / 2000)
    
    return battery_voltage


while True:
    print(read_battery_voltage(adc))
    time.sleep(0.1)
    
    
    
    
    
    
    
    