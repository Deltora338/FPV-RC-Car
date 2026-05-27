# Save this file on your Pi Pico as: max7219.py
from machine import Pin

class SevenSegment:
    def __init__(self, spi, cs, digits=4):
        self.spi = spi
        self.cs = cs
        self.digits = digits
        self.init_display()

    def _write(self, reg, data):
        self.cs.value(0)
        self.spi.write(bytearray([reg, data]))
        self.cs.value(1)

    def init_display(self):
        self._write(0x0C, 0x01) # Shutdown Register: Normal Operation
        self._write(0x0B, self.digits - 1) # Scan Limit: Drive only your 4 digits
        self._write(0x09, 0x0F) # Decode Mode: Code B decode for digits 0–3
        self.brightness(7)
        self.clear()

    def brightness(self, value):
        # Intensity control from 0 (dimmest) to 15 (brightest)
        self._write(0x0A, max(0, min(value, 15)))

    def clear(self):
        for i in range(1, self.digits + 1):
            self._write(i, 0x0F) # 0x0F is the "Blank" character code in Code B

    def display_number(self, num):
        # Formats an integer to fit onto your 4 digits right-aligned
        string_num = f"{num:4d}"[-self.digits:]
        for i, char in enumerate(reversed(string_num)):
            digit_reg = i + 1
            if char == " " or char == "-":
                self._write(digit_reg, 0x0F) # Blank space
            else:
                self._write(digit_reg, int(char))