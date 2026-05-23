from machine import Pin
from time import sleep

IN1 = machine.Pin(2, machine.Pin.OUT)
IN2 = machine.Pin(3, machine.Pin.OUT)
IN3 = machine.Pin(4, machine.Pin.OUT)
IN4 = machine.Pin(5, machine.Pin.OUT)

pins = [IN1, IN2, IN3, IN4]

sequence = [[1,0,0,1],
            [1,1,0,0],
            [0,1,1,0],
            [0,0,1,1]]

def step_motor(steps, direction=1, delay=0.002):
    sequence_len = len(sequence)
    
    #--gemini--
    
    for i in range(steps):
        # Determine which step pattern to use
        step_index = (i * direction) % sequence_len
        current_step = sequence[step_index]
        
        # Apply the high/low states to the pins
        for pin_index in range(4):
            pins[pin_index].value(current_step[pin_index])
            
        # Give the motor time to physically move
        sleep(delay)
        
    # Turn off all coils after movement to save power/prevent heating
    for pin in pins:
        pin.value(0)
        
while True:
    print("Rotating Clockwise...")
    # 2048 steps equals roughly one full 360-degree rotation
    step_motor(2048, direction=1, delay=0.002)
    sleep(1)
    
    print("Rotating Counter-Clockwise...")
    step_motor(2048, direction=-1, delay=0.005)
    sleep(1)