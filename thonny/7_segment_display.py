import machine
import time
from max7219 import SevenSegment 

spi = machine.SPI(0, baudrate=1000000, polarity=0, phase=0, 
                  sck=machine.Pin(18), mosi=machine.Pin(19))

# FIX: Set both digits AND scan_digits to 4
display = SevenSegment(digits=4, scan_digits=4, cs=machine.Pin(17, machine.Pin.OUT)) 
display._spi = spi 

display.brightness(1)

print("Display active! Starting test routine...")

# Test Routine
display.number(5641)

counter = 0
while True:
    display.number(counter)
    
    counter += 1
    if counter > 9999:
        counter = 0
        
    time.sleep(1)
