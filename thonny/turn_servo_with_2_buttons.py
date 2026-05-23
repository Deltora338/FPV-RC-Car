from machine import Pin
from servo import Servo
from time import sleep

my_servo = Servo(16)

button1 = Pin(18, Pin.IN, Pin.PULL_DOWN)
button2 = Pin(19, Pin.IN, Pin.PULL_DOWN)

angle = 90

my_servo.write(angle)

while True:
    if button1.value() == 1 or button2.value() == 1:
        print("here")
        if button1.value() == 1 and button2.value() == 1:
            sleep(0.2)
            continue
        elif button1.value() == 1:
            print(1)
            angle += 10
            my_servo.write(angle)
            sleep(0.2)
        else:
            print(2)
            angle -= 10
            my_servo.write(angle)
            sleep(0.2)
        
        sleep(0.02)