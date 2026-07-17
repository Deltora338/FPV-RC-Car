from machine import Pin, PWM, UART

esc = PWM(Pin(14, Pin.OUT, Pin.PULL_DOWN))
esc.freq(50)
esc.duty_u16(4915)

import time

servo = PWM(Pin(15))
servo.freq(50)

uart0 = UART(0, baudrate=420000, rx=Pin(1), tx=Pin(0))

led = Pin(25, Pin.OUT)
led.value(0)

def steering(angle, servo):
    if angle < 0:
        angle = 0
    elif angle > 180:
        angle = 180
        
    duty = int(1638 + (angle / 180) * (8192 - 1638))
    servo.duty_u16(duty)
    
def throttle(raw_value, esc_pwm):
    if raw_value < 174:
        raw_value = 174
    elif raw_value > 1811:
        raw_value = 1811
        
    # Map 174 -> 1811 (joystick) to 3276 -> 6553 (1ms to 2ms duty cycle)
    duty = int(3276 + ((raw_value - 174) / (1811 - 174)) * (6553 - 3276))
    esc_pwm.duty_u16(duty)

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
    """calculates the CRSF checksum byte"""
    crc = 0
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x80:
                crc = (crc << 1) ^ 0xD5
            else:
                crc <<= 1
        crc &= 0xFF  # Ensure it stays an 8-bit integer
    return crc

def read_control(lss, lsq):
    channels = None
    last_signal_strength = lss
    last_signal_quality = lsq
    
    if uart0.any():
        raw_data = uart0.read()
        data_length = len(raw_data)
        
        i = 0
        while i < (data_length - 4):  # Needs to be at least long enough for a header + lengthte
            # 1. Look for the actual Sync Address (0xC8)
            if raw_data[i] == 0xC8:
                length = raw_data[i+1]
                
                # Make sure we have the full packet in our buffer
                if i + 2 + length <= data_length:
                    # Extract the section that the CRC is calculated on (Type + Payload)
                    # Length includes the CRC byte at the end, so we omit that last byte
                    crc_data = raw_data[i+2 : i+1+length] 
                    expected_crc = raw_data[i+1+length]
                    
                    # 2. Calculate and Validate the CRC
                    if crsf_crc8(crc_data) == expected_crc:
                        # Success! The packet is 100% valid.
                        packet_type = raw_data[i+2]
                        payload = raw_data[i+2 : i+1+length] # Type + Payload
                        
                        if packet_type == 0x16:  # RC Channels Frame
                            channels = decode(payload)
                            
                        elif packet_type == 0x14: # Link Stats Frame
                            stats = decode_signal_data(payload)
                            last_signal_strength = stats['rssi1']
                            last_signal_quality = stats['lq']
                            
                    else:
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
            }
            
    return None

controller_data = {
    'steering': 992,
    'throttle': 992,
    'raw_channels': [992] * 8,
    'last_signal_strength': 0,
    'last_signal_quality': 0
}

print
led.value(1)
esc.duty_u16(4915)
time.sleep(5)
led.value(0)

while True:
    rx_control = read_control(controller_data['last_signal_strength'], controller_data['last_signal_quality'])
    
    if rx_control is not None:
        controller_data = rx_control
        
        raw_steering = controller_data['steering']
        
        steering_angle = round((raw_steering - 174) * (55 - 125) / (1811 - 174) + 125)
        steering(steering_angle, servo)
        
        raw_throttle = controller_data['throttle']
        throttle(raw_throttle, esc)
        
        # Print Debug info
        ch = controller_data['raw_channels']
        print(f'Throttle: {ch[2]}')
        print(f'Steering {abs(ch[0] - 992)} {"left" if (ch[0] - 992) <= 0 else "right"}')
        print(f'Signal: {controller_data["last_signal_strength"]}dBm, {controller_data["last_signal_quality"]}%')
    
    time.sleep(0.01)






