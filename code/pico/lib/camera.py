"""This module contains the [camera].toggle() fucntion which will
toggle the relay that controls power to the vtx
"""

from machine import Pin, ADC
import math

signal_pin = Pin(13, Pin.OUT)
VTX_status_led = Pin(21, Pin.OUT)

adc = ADC(27)

r1 = 10_000
th_r0 = 10_000

class Relay():
    def __init__(self, pin, led) -> None:
        self.pin = pin
        self.led = led
        self.value = 0
    
    def toggle(self) -> None:

        if self.value == 0:
            self.value = 1
            self.pin.value(1)
            self.led.value(1)
        else:
            self.value = 0
            self.pin.value(0)
            self.led.value(0)
    
    def temperature(self) -> float:
        reading = adc.read_u16()
        
        voltage = reading * 2
        
        thermistor_resistence = r1 * ((3.3 / voltage) - 1)
        
        temperature = 1 / ((1 / 298.15) + (1/3950) * math.log(thermistor_resistence / 10_000)) - 273.15
            

VTX_relay = Relay(signal_pin, VTX_status_led)

