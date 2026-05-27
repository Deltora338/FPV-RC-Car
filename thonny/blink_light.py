from machine import Pin
import time

# built in LED
led = Pin(25, Pin.OUT)


try:
    led.toggle()

    while True:
        led.toggle()
        time.sleep(1)
        
finally:
    led.value(0)
    print("Complete")
    
    