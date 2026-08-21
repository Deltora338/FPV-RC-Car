"""This file contains constants and pin definitions which are imported
used in main.py
"""

from machine import Pin, PWM, UART, ADC
import time, json


class Main():
    def __init__(self, start_time) -> None:
        self.start_time = start_time
        
        # servo and esc PWM pins
        self.servo = PWM(Pin(15, Pin.OUT, Pin.PULL_DOWN))
        self.servo.freq(50)
        self.esc = PWM(Pin(2, Pin.OUT, Pin.PULL_DOWN))
        self.esc.freq(50)

        # both uart modules with the
        self.uart_elrs = UART(0, baudrate=420000, rx=Pin(1, Pin.IN, Pin.PULL_DOWN), tx=Pin(0, Pin.OUT, Pin.PULL_DOWN))  # control elrs
        self.uart_telem = UART(1, baudrate=57600, rx=Pin(9, Pin.IN, Pin.PULL_DOWN), tx=Pin(8, Pin.OUT, Pin.PULL_DOWN)) # telemetry link

        # adc pins (battery and temp voltage dividers)
        self.battery_adc_pin = ADC(28)

        self.boot_led = Pin(25, Pin.OUT) # 16

        self.relay = Pin(14, Pin.OUT, value=1)

        # default for self.initialse
        self.battery_voltage = None
        self.last_battery_read_time = 0
        
        self.lss = None
        self.lsq = None
        self.is_armed = False
        
        self.esc.duty_u16(4915)
        
        self.last_telemetry_time = 0
        
        self.camera_start_time = 0
        self.is_camera_on = False
        self.allow_camera = False
        self.camera_control_state = False
        
        self.allowance_remaining = 0
        self.cooldown_remaining = 0
        
        try:
            with open("camera_allowance_variable.txt", "x") as file:
                file.write("0") # assume no allowance for safety
            self.camera_allowance = 0
        except OSError:
            with open("camera_allowance_variable.txt", 'r') as file:
                self.camera_allowance = float(file.read())
        
        self.camera_cooldown = 300 # 300 sec, 5 min
        self.camera_cooldown_start_time = 0
        
        self.elrs_connection = None
    

    def _save_camera_allowance(self):
        try:
            with open("camera_allowance_variable.txt", "w") as f:
                f.write(str(self.camera_allowance))
        except OSError:
            pass 
 
 
    def relay_update(self):
        now = time.time()
        if self.is_camera_on:
            # camera is on
            self.allowance_remaining = max(0, self.camera_allowance - (now - self.camera_start_time))
            self.cooldown_remaining = 0
            elapsed = now - self.camera_start_time
            if elapsed >= self.camera_allowance:
                self._force_off()
                self.camera_cooldown_start_time = now
                self.allow_camera = False
        elif not self.allow_camera:
            # on cooldown
            self.cooldown_remaining = max(0, self.camera_cooldown - (now - self.camera_cooldown_start_time))
            self.allowance_remaining = 0
            if now - self.camera_cooldown_start_time >= self.camera_cooldown:
                self.allow_camera = True
                self.camera_allowance = 180
                self._save_camera_allowance()
        else:
            # camera off, allowed, not on cooldown
            self.allowance_remaining = self.camera_allowance
            self.cooldown_remaining = 0


    def relay_on(self):
        """Called when the camera is wanted on"""
        if not self.allow_camera or self.is_camera_on:
            return
        self.relay.init(Pin.OUT, value=0)
        self.is_camera_on = True
        self.camera_start_time = time.time()


    def relay_off(self):
        """Called to turn the camera off and reset/change/save allowance and cooldown variables"""
        if not self.is_camera_on:
            return
        self.relay.init(Pin.IN)
        self.is_camera_on = False
        elapsed = time.time() - self.camera_start_time
        self.camera_allowance = max(0, self.camera_allowance - elapsed)
        self._save_camera_allowance()
        if self.camera_allowance <= 0:
            self.camera_cooldown_start_time = time.time()
            self.allow_camera = False

    def _force_off(self):
        """Helper for turning running camera off"""
        self.relay.init(Pin.IN)
        self.is_camera_on = False
        self.camera_allowance = 0
        self._save_camera_allowance()
    
    
    def read_battery_voltage(self, now=False) -> None:
        """Updates self.battery_voltage when called from asoc adc pin if it has been sufficiently long"""
        if time.ticks_diff(time.ticks_ms(), self.last_battery_read_time) >= 2000 or now:
            total = 0
            for _ in range(10):
                total += self.battery_adc_pin.read_u16()
            
            reading = total // 10
            
            # voltage at adc_pin
            pin_voltage = (reading / 65535) * 3.3
            
            # pin voltage converted back to the correlated battery voltage
            battery_voltage = pin_voltage * ((10000 + 2000) / 2000)
            
            if battery_voltage < 8:
                self.battery_voltage = 0
            else:
                self.battery_voltage = battery_voltage
            
            
            self.last_battery_read_time = time.ticks_ms()
        
        time.sleep_ms(10)
    

    def steering(self, angle) -> None:
        if angle < 60:
            angle = 60
        elif angle > 120:
            angle = 120
                
        duty = int(1637 + (angle / 180) * (8192 - 1638))
        self.servo.duty_u16(duty)
            
            
    def throttle(self, raw_value, gear_value, range_) -> None:
        if raw_value < 174:
            raw_value = 174
        elif raw_value > 1811:
            raw_value = 1811
        
        if gear_value > 1000:
                gear = "drive"
        elif gear_value < 500:
            gear = "reverse"
        else:
            gear = "neutral"
            
        if range_ > 1000:
            range_multiplier = 1.0
        else:
            range_multiplier = 0.5
            
        # map joystick range (1811 - 174), to 3276 - 6553 (1ms to 2ms PWM signal)
            
        if gear == 'drive':
            duty = ((raw_value - 174) * range_multiplier) + 4915 
        elif gear == 'reverse':
            duty = 4915 - ((raw_value - 174) * range_multiplier)
        else:  # neutral or fallback
            duty = 4915
                                    
        self.esc.duty_u16(int(duty))
                

    def crsf_crc8(self, data: bytes) -> int:
        """calculates the CRSF checksum byte.
        This code was taken from the CRSF protocol documentation."""
        crc = 0
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = (crc << 1) ^ 0xD5
                else:
                    crc <<= 1
            crc &= 0xFF
        return crc
    
    
    def read_control(self):
        channels = None
        
        if self.uart_elrs.any():
            raw_data = self.uart_elrs.read()
            data_length = len(raw_data)
            
            i = 0
            while i < (data_length - 4):  # needs to be at least long enough for a header + length byte + sync + crc

                # check for crsf header
                if raw_data[i] == 0xC8:
                    length = raw_data[i+1]
                    
                    # check length is valid
                    if i + 2 + length <= data_length:
        
                        # take the part of the packet that crc is calculated on
                        # and the crc that is transmitted with the packet
        
                        crc_data = raw_data[i+2 : i+1+length] 
                        expected_crc = raw_data[i+1+length]
                        
                        # calculate and compare the crc
                        if self.crsf_crc8(crc_data) == expected_crc:

                            packet_type = raw_data[i+2]
                            payload = raw_data[i+2 : i+1+length] # type + Payload
                            
                            if packet_type == 0x16:  # control frame
                                data = payload[1:]
                                
                                channels = [0] * 8
        
                                channels[0] = (data[0] | (data[1] << 8)) & 0x07FF
                                # channels[1] = (data[1] >> 3 | data[2] << 5) & 0x07FF
                                channels[2] = ((data[2] >> 6) | (data[3] << 2) | (data[4] << 10)) & 0x07FF
                                # channels[3] = (data[4] >> 1 | data[5] << 7) & 0x07FF
                                channels[4] = ((data[5] >> 4) | (data[6] << 4)) & 0x07FF
                                channels[5] = ((data[6] >> 7) | (data[7] << 1) | (data[8] << 9)) & 0x07FF
                                channels[6] = ((data[8] >> 2) | (data[9] << 6)) & 0x07FF
                                channels[7] = ((data[9] >> 5) | (data[10] << 3)) & 0x07FF
                                
                            elif packet_type == 0x14: # link stats frame
                                self.lss = -payload[1]
                                self.lsq = payload[3]
                                
                        else:
                            # crc mismatch, ignore packet
                            pass
                        
                        i += 2 + length
                        continue
                i += 1
                
            if channels is not None:
                return {
                    'steering': channels[0],
                    'throttle': channels[2],
                    'raw_channels': channels,
                    'last_signal_strength': self.lss,
                    'last_signal_quality': self.lsq,
                    "armed": channels[4],
                    "gear": channels[5],
                    "throttle_range": channels[6],
                    "camera": channels[7],
                }
                
        return None
    
    
    def initialise(self):
        self.relay_off()
        self.boot_led.value(0)
        while (self.battery_voltage is None) or  (self.elrs_connection is None):
            self.read_battery_voltage(True)
            data = self.read_control()
            if data is not None:
                self.elrs_connection = data["last_signal_strength"]
            
            time.sleep(0.01)
        
        self.relay_off()
    
    
    def control(self):
        data = self.read_control()
        if data is not None:
            steering_angle = ((data["steering"] - 174) * 60 / (1811 - 174)) + 60
            if data is not None:
                if data["armed"] > 1000:
                    self.is_armed = True
                    self.throttle(data["throttle"], data["gear"], data["throttle_range"])
                    self.steering(steering_angle)
                    
                    if data["camera"] > 1000:
                        self.camera_control_state = True
                    else:
                        self.camera_control_state = False
                else:
                    self.is_armed = False


    def telemetry(self) -> None:
        if time.ticks_diff(time.ticks_ms(), self.last_telemetry_time) >= 200:
            logs = None
            try:
                with open("error_log.txt", "r") as file:
                    logs = file.read()
            except Exception as e:
                pass
            
            if self.battery_voltage < 9:
                battery_info = "battery not connected"
            else:
                battery_info = self.battery_voltage
            
            telemetry_data = {
                "battery voltage" : battery_info,
                "camera allowance" : round(self.camera_allowance, 1),
                "camera cooldown" : round(self.camera_cooldown, 1),
                "elrs connection" : self.lss,
                "error logs" : logs,
                "uptime" : int(time.time() - self.start_time)
                }
            
            msg = json.dumps(telemetry_data) + "\n"
            msg = msg.encode('utf-8')
            self.uart_telem.write(msg)
            
            print(msg)
            
            self.last_telemetry_time = time.ticks_ms()
        
        time.sleep_ms(10)
        
    
    def mainloop(self):
        while True:
            self.read_battery_voltage()
            self.control()
            if self.camera_control_state:
                self.relay_on()
            else:
                self.relay_off()
            self.relay_update()
            self.telemetry()
            
            


