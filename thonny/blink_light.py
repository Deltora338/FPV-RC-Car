from machine import Pin
import time

# Built-in LED on most Pico boards is pin 25 (Pico 2 uses Pin 25 as well, Pico W uses 'LED')
led = Pin(25, Pin.OUT)

for i in range(10):
    led.toggle()
    time.sleep(0.1)

while True:
    led.toggle()
    time.sleep(0.5)  # Pause for half a second