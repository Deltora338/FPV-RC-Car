import machine
import time

# 1. Setup SPI and CS Pin explicitly
spi = machine.SPI(0, baudrate=1000000, polarity=0, phase=0, 
                  sck=machine.Pin(18), mosi=machine.Pin(19))
cs = machine.Pin(17, machine.Pin.OUT)

def send_cmd(reg, data):
    cs.value(0)          # Select chip
    spi.write(bytearray([reg, data]))
    cs.value(1)          # Deselect chip (latches data)

# 2. Hardware Reset / Initialization Sequence
send_cmd(0x0C, 0x01)  # Shutdown Register: Normal Operation (Turn ON)
send_cmd(0x0B, 0x03)  # Scan Limit Register: Display digits 0-3 (4 digits)
send_cmd(0x0A, 0x02)  # Intensity Register: Low brightness (prevents brownout)
send_cmd(0x09, 0x00)  # Decode Mode: No decode (we manually light up segments)

print("Hardware configured. Sending data...")

while True:
    # Light up the middle safe segment (G) on all 4 digits
    send_cmd(0x01, 0x01) # Digit 0
    send_cmd(0x02, 0x01) # Digit 1
    send_cmd(0x03, 0x01) # Digit 2
    send_cmd(0x04, 0x01) # Digit 3
    time.sleep(1)