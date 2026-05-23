from machine import Pin
import time

button = Pin(0, Pin.IN, Pin.PULL_DOWN)

pin1 = Pin(21, Pin.OUT)
pin2 = Pin(20, Pin.OUT)
pin3 = Pin(19, Pin.OUT)
pin4 = Pin(18, Pin.OUT)
pin5 = Pin(17, Pin.OUT)
pin6 = Pin(16, Pin.OUT)


lights = []
lights.append(pin1)
lights.append(pin2)
lights.append(pin3)
lights.append(pin4)
lights.append(pin5)
lights.append(pin6)


def update_lights(value, lights) -> None:
    print(value)
    if value >= 64:
        print("value >= 64")
        return

    for i in range(6):
            # Use bitwise shift and AND to check if the i-th bit is set
            bit = (value >> i) & 1
            lights[i].value(bit)

            

light_value = 0
try:
    while True:
            if button.value() == 1:
                light_value += 1
                if light_value > 63:
                    light_value = 0
                    update_lights(light_value, lights)
                else:
                    update_lights(light_value, lights)

            time.sleep(0.1)

finally:
    for pin in lights:
        pin.value(0)
