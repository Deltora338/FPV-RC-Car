import machine
import time

# 1. Setup Joystick and Servo
x_axis = machine.ADC(machine.Pin(26))
servo = machine.PWM(machine.Pin(15))
servo.freq(50)

# 2. Updated Servo Limits based on your hardware (using duty_u16)
SERVO_MIN = 2000    # 0 degrees (Far Left)
SERVO_MAX = 8000    # 180 degrees (Far Right)
# Calculate the exact midpoint between 2000 and 8000
SERVO_MID = int((SERVO_MIN + SERVO_MAX) / 2) # Results in 5000 (90 degrees)

# 3. Your Joystick Calibration Values
JOY_MIN = 0
JOY_CENTER = 50000 
JOY_MAX = 65535
DEADZONE = 500 

def map_value(value, in_min, in_max, out_min, out_max):
    """Standard mapping function"""
    return int((value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)

print("Running with 2000-8000 u16 servo range...")

while True:
    x_val = x_axis.read_u16()
    
    # Check if joystick is resting in the deadzone
    if abs(x_val - JOY_CENTER) <= DEADZONE:
        servo_pos = SERVO_MID
        
    # Joystick is pushed LEFT (0 to 50000)
    elif x_val < JOY_CENTER:
        # Maps the left stick range to servo range 2000 -> 5000
        servo_pos = map_value(x_val, JOY_MIN, JOY_CENTER, SERVO_MIN, SERVO_MID)
        
    # Joystick is pushed RIGHT (50000 to 65535)
    else:
        # Maps the right stick range to servo range 5000 -> 8000
        servo_pos = map_value(x_val, JOY_CENTER, JOY_MAX, SERVO_MID, SERVO_MAX)
    
    # Send the u16 position to the servo
    servo.duty_u16(servo_pos)
    
    time.sleep(0.02)