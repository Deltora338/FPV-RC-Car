"""Main file which imports and runs the main loop code
"""

from machine import Pin, PWM, UART
import time
from config import *

servo.freq(50)

esc.freq(50)  # standard freq
esc.duty_u16(ESC_DUTY_NEUTRAL)  # neutral duty cycle

boot_led.value(0)
main_led.value(1)

while True:
    rx_control = read_control(controller_data['last_signal_strength'],
                              controller_data['last_signal_quality'])
    
    if rx_control is not None:
        controller_data = rx_control
        
        raw_steering = controller_data['steering']
        
        # gear lever either 174, 992 or 1811
        if controller_data['gear'] > 1000:
            gear = "reverse"
        elif controller_data['gear'] < 500:
            gear = "drive"
        else:
            gear = "neutral"
        
        steering_angle = round((raw_steering - JOYSTICK_MIN) * (55 - 125) / (JOYSTICK_RANGE) + 125)
        steering((180 - steering_angle), servo) # servo is mounted upside down, so invert the input
        
        raw_throttle = controller_data['throttle']
        throttle(raw_throttle, esc, gear)
        
        # print Debug info
        ch = controller_data['raw_channels']
        print(f'Throttle: {ch[2]}')
        print(f'Steering {abs(ch[0] - 992)} {"left" if (ch[0] - 992) <= 0 else "right"}')
        # print(f'Signal: {controller_data["last_signal_strength"]}dBm, {controller_data["last_signal_quality"]}%')
    
    time.sleep(0.01)


