import machine, time
from servo import Servo

potentiometer = machine.ADC(26)

my_servo = Servo(16)

while True:
    raw_reading = potentiometer.read_u16()
    
    voltage = (raw_reading / 65535) * 3.3
    
    print(f"Raw Value: {raw_reading} | Voltage: {voltage:.2f}V")
    
    my_servo.write((180/3.3) * voltage)
    
    # Small delay to keep the serial output readable
    time.sleep(0.1)