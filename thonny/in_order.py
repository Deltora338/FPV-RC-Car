from machine import Pin
from time import sleep

button = Pin(0, Pin.IN, Pin.PULL_DOWN)

white = Pin(20, Pin.OUT)
blue = Pin(19, Pin.OUT)
green = Pin(18, Pin.OUT)
yellow = Pin(17, Pin.OUT)
red = Pin(16, Pin.OUT)

assert red.value() == 0

try:
    while True:
        if button.value() == 1:
            print("pressed", "white")
            white.value(1)
            sleep(0.5)
            print("blue")
            white.value(0)
            blue.value(1)
            sleep(0.5)
            print("green")
            blue.value(0)
            green.value(1)
            sleep(0.5)
            print("yellow")
            green.value(0)
            yellow.value(1)
            sleep(0.5)
            print("red")
            yellow.value(0)
            red.value(1)
            sleep(0.5)
            red.value(0)
            print("done")
        else:
            print("no")
        
        sleep(0.05)
        
finally:
    pass
