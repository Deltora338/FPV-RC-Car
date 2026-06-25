import serial
import time

ser = serial.Serial('COM10', 420000, timeout=1)

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
    return {
        "rssi1": -payload[1],
        "rssi2": -payload[2],
        "lq": payload[3]
    }

last_signal_strength = 0
last_signal_quality = 0

buf = bytearray()

while True:
    # Drain whatever is available and append to buffer
    waiting = ser.in_waiting
    if waiting:
        buf += ser.read(waiting)
    
    # Process all complete frames in the buffer
    i = 0
    while i < len(buf):
        # CRSF frame: [sync] [length] [type] [payload...] [crc]
        # sync byte is 0xC8 (from FC) or 0xEE (from TX) — but your Pico used 0x16/0x14 as type bytes
        # so we look for the frame where buf[i] is the sync, buf[i+1] is length
        
        if i + 2 >= len(buf):
            break  # need more data
        
        sync = buf[i]
        if sync not in (0xC8, 0xEE):
            i += 1
            continue
        
        frame_len = buf[i + 1]  # length includes type + payload + crc, not sync or length itself
        total_frame = 2 + frame_len  # sync + length byte + rest
        
        if i + total_frame > len(buf):
            break  # frame not complete yet, wait for more data
        
        frame_type = buf[i + 2]
        payload = buf[i + 2 : i + total_frame - 1]  # exclude crc at end

        if frame_type == 0x16 and len(payload) >= 22:
            channels = decode(payload)
            print(f'\nJoysticks (x, y): ({channels[3]}, {channels[2]}), ({channels[0]}, {channels[1]})')
            print(f'Switches:         [{channels[4]}], [{channels[5]}], [{channels[6]}], [{channels[7]}]')
            print(f'Signal: {last_signal_strength}dBm, {last_signal_quality}%')
        
        elif frame_type == 0x14 and len(payload) >= 4:
            stats = decode_signal_data(payload)
            last_signal_strength = stats['rssi1']
            last_signal_quality = stats['lq']
        
        i += total_frame
    
    # Keep only unprocessed bytes
    buf = buf[i:]
    time.sleep(0.1)
