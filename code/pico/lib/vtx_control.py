"""This module contains the [camera].toggle() fucntion which will
toggle the relay that controls power to the vtx
"""

from machine import Pin, ADC
import math

camera_relay_signal_pin = Pin(13, Pin.OUT)
VTX_status_led = Pin(21, Pin.OUT)

r1 = 10_000
th_r0 = 10_000

class Camera():
    def __init__(self, pin, led, sensor=27) -> None:
        self.pin = pin
        self.led = led
        self.value = 0
        self.sensor_pin = sensor
        self.adc = ADC(sensor)
    
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
        reading = self.adc.read_u16()
        
        voltage = reading * 2
        
        thermistor_resistence = r1 * ((3.3 / voltage) - 1)
        
        temperature = 1 / ((1 / 298.15) + (1/3950) * math.log(thermistor_resistence / 10_000)) - 273.15
        
        return temperature

