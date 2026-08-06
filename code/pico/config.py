"""This file contains constants and pin definitions which are imported
used in main.py
"""

from machine import Pin, PWM, UART

# servo and esc PWM pins
servo = PWM(Pin(15, Pin.OUT, Pin.PULL_DOWN))
esc = PWM(Pin(2, Pin.OUT, Pin.PULL_DOWN))  # pull down resistor to eliminate noise on the line

# both uart modules with the
uart_elrs = UART(0, baudrate=420000, rx=Pin(1, Pin.IN, Pin.PULL_DOWN), tx=Pin(0, Pin.OUT, Pin.PULL_DOWN))  # control elrs
uart_telem = UART(1, baudrate=57600, rx=Pin(5, Pin.IN, Pin.PULL_DOWN), tx=Pin(4, Pin.OUT, Pin.PULL_DOWN)) # telemetry link

# default data that remains until new control data is recieved
controller_data = {
    'steering': 992,
    'throttle': 174,
    'gear' : 992,
    'armed' : 174,
    'raw_channels': [992] * 8,
    'last_signal_strength': 0,
    'last_signal_quality': 0
}

# joytick constants
JOYSTICK_MIN = 174
JOYSTICK_MAX = 1811
JOYSTICK_RANGE = 1811 - 174

# neutral duty value for esc
ESC_DUTY_NEUTRAL = 4915


# status leds
boot_led = Pin(25, Pin.OUT) # 16
main_led = Pin(17, Pin.OUT) # 17
control_led = Pin(18, Pin.OUT)
telem_led = Pin(19, Pin.OUT)

low_voltage_led = Pin(20, Pin.OUT)
camera_relay_signal_pin = Pin(13, Pin.OUT)
VTX_status_led = Pin(21, Pin.OUT)
VTX_temp_led = Pin(22, Pin.OUT)


