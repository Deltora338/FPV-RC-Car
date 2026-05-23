from machine import Pin
import time

# Built-in LED on most Pico boards is pin 25 (Pico 2 uses Pin 25 as well, Pico W uses 'LED')
led = Pin(25, Pin.OUT)

powerPin = Pin(15, Pin.OUT)

outputPin = Pin(14, Pin.OUT)
inputPin = Pin(16, Pin.IN)

try:
    led.value(1)
    outputPin.value(1)

    while True:
        if not inputPin:
            powerPin.value(1)
        else:
            powerPin.value(0)

        time.sleep(0.01)
        
finally:
    led.value(0)
    print("exited")
    
    