"""This file contains constants and pin definitions which are imported
used in main.py
"""

from machine import Pin, PWM, UART, ADC
import lib, math, time, json


class Main():
    def __init__(self) -> None:
        # servo and esc PWM pins
        self.servo = PWM(Pin(15, Pin.OUT, Pin.PULL_DOWN))
        self.esc = PWM(Pin(2, Pin.OUT, Pin.PULL_DOWN))  # pull down resistor to eliminate noise on the line

        # both uart modules with the
        self.uart_elrs = UART(0, baudrate=420000, rx=Pin(1, Pin.IN, Pin.PULL_DOWN), tx=Pin(0, Pin.OUT, Pin.PULL_DOWN))  # control elrs
        self.uart_telem = UART(1, baudrate=57600, rx=Pin(5, Pin.IN, Pin.PULL_DOWN), tx=Pin(4, Pin.OUT, Pin.PULL_DOWN)) # telemetry link

        # adc pins (battery and temp voltage dividers)
        self.battery_adc_pin = ADC(28)
        self.vtx_temp_adc_pin = ADC(26)

        # status leds
        self.boot_led = Pin(25, Pin.OUT) # 16
        self.main_led = Pin(17, Pin.OUT) # 17
        self.control_led = Pin(18, Pin.OUT)
        self.telem_led = Pin(19, Pin.OUT)

        self.low_voltage_led = Pin(20, Pin.OUT)
        self.relay = Pin(13, Pin.OUT)
        self.VTX_status_led = Pin(21, Pin.OUT)
        self.VTX_temp_led = Pin(22, Pin.OUT)

        # default for self.initialse
        self.battery_voltage = None
        self.vtx_temp = None
        
        self.lss = None
        self.lsq = None
        
        self.esc.duty_u16(duty)
        
        self.last_telemetry_time = 0
        
    def relay_on(self):
        self.relay.init(Pin.OUT, value=0)   # drive low, sinks current, relay ON

    def relay_off(self):
        self.relay.init(Pin.IN)

    
    def read_battery_voltage(self) -> float:
        total = 0
        for _ in range(10):
            total += self.battery_adc_pin.read_u16()
        
        reading = total // 10
        
        # voltage at adc_pin
        pin_voltage = (reading / 65535) * 3.3
        
        # pin voltage converted back to the correlated battery voltage
        battery_voltage = pin_voltage * ((10000 + 2000) / 2000)
        
        return battery_voltage
    

    def read_vtx_temp(self) -> float:
        total = 0
        for _ in range(10):
            total += self.vtx_temp_adc_pin.read_u16()
        
        reading = total // 10
        
        # voltage at adc_pin
        v_out = (reading / 65535) * 3.3
        
        r_ntc = 10000 * ((5 / v_out) - 1.0)

        # Steinhart-Hart / Beta Parameter Equation
        # 1/T = 1/T25 + (1/B) * ln(R / R25)
        temp_kelvin = 1.0 / ((1.0 / 298.15) + (math.log(r_ntc / 10000) / 3950.0))
        temp_celsius = temp_kelvin - 273.15
        
        return temp_celsius
    

    def steering(self, angle) -> None:
        if angle < 30:
            angle = 30
        elif angle > 150:
            angle = 150
                
        duty = int(1637 + (angle / 180) * (8192 - 1638))
        self.servo.duty_u16(duty)
            
            
    def throttle(self, raw_value, gear_value) -> None:
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
            
        # map joystick range (1811 - 174), to 3276 - 6553 (1ms to 2ms PWM signal)
            
        if gear == 'drive':
            duty = (raw_value - 174) + 4915 
        elif gear == 'reverse':
            duty = 4915 - (raw_value - 174)
        else:  # neutral or fallback
            duty = 4915
                

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
                                
                            elif packet_type == 0x1E: # link stats frame
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
        self.boot_led.value(0)
        self.main_led.value(1)
        while (self.battery_voltage is None) or (self.vtx_temp is None) or (self.elrs_connection is None):
            self.read_battery_voltage = self.read_battery_voltage()
            self.read_vtx_temp = self.vtx_temp()
            data = self.read_control()
            if data is not None:
                self.elrs_connection = data["last_signal_strength"]
        
        self.relay_off()
    
    
    def control(self):
        data = self.read_control()
        if data is not None:
            self.throttle(data["throttle"], data["gear"])
            self.steering(data["steering"])
    
    def telemetry(self) -> None:
        if self.uart_telem.any():
            telemetry = self.uart_telem.readline()
            if telemetry:
                data_str = telemetry.decode('utf-8').strip()
                
                control = json.loads(data_str)
                
                steering = control.get("steering", 0)
                throttle = control.get("throttle", 0)
                gear = control.get("gear", 0)
                
                if throttle and gear:
                    self.throttle(throttle, gear)
                
                if steering:
                    self.steering(steering)
        
        if time.ticks_diff(time.ticks_ms(), last_telemetry_time) >= 200:
            logs = None
            try:
                with open("error_log.txt", "r") as file:
                    logs = file.read()
                # Clear contents after reading
                with open("error_log.txt", "w") as file:
                    file.write("")
            except Exception as e:
                logs = f"Error reading log: {e}"
                
            telemetry_data = {
                "battery voltage" : self.read_battery_voltage(),
                "vtx temp" : self.read_vtx_temp(),
                "error logs" : logs
                }
            
            msg = json.dumps(telemetry_data) + "\n"
            self.uart_telem.write(msg.encode('utf-8'))
            
            last_telemetry_time = time.ticks_ms()
        
        time.sleep_ms(10)
        
    
    def mainloop(self):
        while True:
            self.read_battery_voltage()
            self.read_vtx_temp()
            self.control()
            self.telemetry()
