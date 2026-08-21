

def decode(payload) -> list[int]:
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

def steering(angle, select_servo) -> None:
    if angle < 0:
        angle = 
    elif angle > 180:
        angle = 180
            
    duty = int(1637 + (angle / 180) * (8192 - 1638))
    select_servo.duty_u16(duty)
        
def throttle(raw_value, esc_, gear_value) -> None:
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
            
    esc_.duty_u16(duty)

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

    def control(lss, lsq, uart_elrs):
        channels = None

        last_signal_strength = lss
        last_signal_quality = lsq
        
        if uart_elrs.any():
            raw_data = uart_elrs.read()
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
                    "armed": channels[4],
                    "gear": channels[5],
                    "switch3": channels[6],
                    "switch4": channels[7],
                }
                
        return None