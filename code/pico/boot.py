'''The ESC needs to recieve a 2 second neutral throttle pulse
almost immediatly ofter powerup to arm, or else it will lock itself out.
This is why the esc pin is defined and used before importing time,
otherwise we miss the window'''

from machine import Pin, PWM

esc = PWM(Pin(2, Pin.OUT, Pin.PULL_DOWN))  # pull down resistor to eliminate electrical noise on the line
esc.freq(50)  # standard freq
esc.duty_u16(4915)  # neutral duty cycle

import time

led = Pin(25, Pin.OUT)
led.value(1)

time.sleep(4)
led.value(0)

