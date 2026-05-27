import machine
from time import sleep

potentiometer = machine.ADC(26)

while True:
    raw_reading = potentiometer.read_u16()
    
    voltage = (raw_reading / 65535) * 3.3
    
    print(f"Raw Value: {raw_reading} | Voltage: {voltage:.2f}V")
    
    sleep(0.05)