from machine import Pin, PWM, UART
import time

servo = PWM(Pin(15, Pin.OUT, Pin.PULL_DOWN))
servo.freq(50)

esc = PWM(Pin(14, Pin.OUT, Pin.PULL_DOWN))  # pull down resistor to eliminate noise on the line
esc.freq(50)  # standard freq
esc.duty_u16(4915)  # neutral duty cycle

uart0 = UART(0, baudrate=420000, rx=Pin(1), tx=Pin(0))  # control elrs

led = Pin(25, Pin.OUT)
led.value(1)

def steering(angle, select_servo):
    if angle < 0:
        angle = 0
    elif angle > 180:
        angle = 180
        
    duty = int(1637 + (angle / 180) * (8192 - 1638))
    select_servo.duty_u16(duty)
    
def throttle(raw_value, esc_):
    if raw_value < 174:
        raw_value = 174
    elif raw_value > 1811:
        raw_value = 1811
        
    # map joystick accross range 1811 - 174, to 3276 - 6553 (1ms to 2ms PWM signal)
    duty = int(3276 + ((raw_value - 174) / (1637)) * (6553 - 3276))
    esc_.duty_u16(duty)

def decode(payload):
    data = payload[1:]
    
    channels = [0] * 8
    
    channels[0] = (data[0] | (data[1] << 8)) & 0x07FF
    channels[1] = (data[1] >> 3 | data[2] << 5) & 0x07FF
    channels[2] = ((data[2] >> 6) | (data[3] << 2) | (data[4] << 10)) & 0x07FF
    channels[3] = (data[4] >> 1 | data[5] << 7) & 0x07FF
    channels[4] = ((data[5] >> 4) | (data[6] << 4)) & 0x07FF
    channels[5] = ((data[6] >> 7) | (data[7] << 1) | (data[8] << 9)) & 0x07FF
    channels[6] = ((data[8] >> 2) | (data[9] << 6)) & 0x07FF
    channels[7] = ((data[9] >> 5) | (data[10] << 3)) & 0x07FF

    return channels

def decode_signal_data(payload):
    # dBm
    
    uplink_rssi1 = -payload[1]
    uplink_rssi2 = -payload[2]
    link_quality = payload[3]  
    
    return {
        "rssi1": uplink_rssi1,
        "rssi2": uplink_rssi2,
        "lq": link_quality
    }

def crsf_crc8(data: bytes) -> int:
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

def read_control(lss, lsq):
    channels = None
    last_signal_strength = lss
    last_signal_quality = lsq
    
    if uart0.any():
        raw_data = uart0.read()
        data_length = len(raw_data)
        
        i = 0
        while i < (data_length - 4):  # needs to be at least long enough for a header + lengthte
            # check for crsf header
            if raw_data[i] == 0xC8:
                length = raw_data[i+1]
                
                # check length is valid
                if i + 2 + length <= data_length:
                    # take the part that crc is calculated on
                    # and the crc that is transmitted with the packet
                    crc_data = raw_data[i+2 : i+1+length] 
                    expected_crc = raw_data[i+1+length]
                    
                    # calculate and compare the crc
                    if crsf_crc8(crc_data) == expected_crc:
                        packet_type = raw_data[i+2]
                        payload = raw_data[i+2 : i+1+length] # type + Payload
                        
                        if packet_type == 0x16:  # control frame
                            channels = decode(payload)
                            
                        elif packet_type == 0x1E: # link stats frame
                            stats = decode_signal_data(payload)
                            last_signal_strength = stats['rssi1']
                            last_signal_quality = stats['lq']
                            
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
                'last_signal_strength': last_signal_strength,
                'last_signal_quality': last_signal_quality,
                "switch1": channels[4],
                "switch2": channels[5],
                "switch3": channels[6],
                "switch4": channels[7],
            }
            
    return None

controller_data = {
    'steering': 992,
    'throttle': 992,
    'raw_channels': [992] * 8,
    'last_signal_strength': 0,
    'last_signal_quality': 0
}

esc.duty_u16(4915)
time.sleep(5)
led.value(0)

while True:
    rx_control = read_control(controller_data['last_signal_strength'], controller_data['last_signal_quality'])
    
    if rx_control is not None:
        controller_data = rx_control
        
        raw_steering = controller_data['steering']
        
        steering_angle = round((raw_steering - 174) * (55 - 125) / (1811 - 174) + 125)
        steering((180 - steering_angle), servo) # servo is mounted upside down
        
        raw_throttle = controller_data['throttle']
        throttle(raw_throttle, esc)
        
        # print Debug info
        ch = controller_data['raw_channels']
        # print(f'Throttle: {ch[2]}')
        # print(f'Steering {abs(ch[0] - 992)} {"left" if (ch[0] - 992) <= 0 else "right"}')
        # print(f'Signal: {controller_data["last_signal_strength"]}dBm, {controller_data["last_signal_quality"]}%')
    
    time.sleep(0.01)
