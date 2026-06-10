# raspberry pi pico 2021
import machine
import time

# set pins for the three lights
# use GP (general purpose) pins connected to their asoc pin via a 200 - 300 ohm resistor
drive_light = machine.Pin(18, machine.Pin.OUT)
neutral_light = machine.Pin(19, machine.Pin.OUT)
reverse_light = machine.Pin(20, machine.Pin.OUT)

# set the two input pins for the joystick
# the joystick give a analog voltage as an input so ADC pins must be used
x_input = machine.ADC(26)
y_input = machine.ADC(27)

# set the pin which will communicate with the servo using PWM
servo = machine.PWM(machine.Pin(15))

# set the frequency as per second
servo.freq(50)  # 20ms

# set servo to middle point

SERVO_MAX = 8000  # servo max
SERVO_MIN = 2000  # servo min

def convert_range(x, servo_min, servo_max, _min=0, _max=2**16):
    '''Takes a number x, a servo's range and x's range
    and returns a number between servo_min and servo_max which is proportional to x in x_min to x_max
    '''
    value = round(servo_min + (servo_max - servo_min) * x / (_max - _min))  # converts to servo's range
    value /= 1000  # divide by 1000
    value = int(value)  # truncate the value
    return value * 1000  # convert back into servo_min to servo_max range

try:
    while True:
        # get x and y values from joystick as numbers from 0 - 65 (integers)
        x = int(x_input.read_u16() / 1000)
        y = int(y_input.read_u16() / 1000)
        print(convert_range(y_input.read_u16(), SERVO_MIN, SERVO_MAX))
        # send servo value to servo
        servo.duty_u16(convert_range(y_input.read_u16(), SERVO_MIN, SERVO_MAX))
        
        if x > 36:
            neutral_light.value(0)
            drive_light.value(0)
            reverse_light.value(1)
        elif x < 28:
            neutral_light.value(0)
            drive_light.value(1)
            reverse_light.value(0)
        else:
            neutral_light.value(1)
            drive_light.value(0)
            reverse_light.value(0)
            
        time.sleep(0.05)
finally:
    neutral_light.value(0)
    drive_light.value(0)
    reverse_light.value(0)

