from machine import UART, Pin
import time

# set uart to gp 1 and 0
uart0 = UART(0, baudrate=420000, tx=Pin(0), rx=Pin(1))

def decode(payload):
    # cut off the stuff at the start (type byte I believe)
    data = payload[1:]
    # set up channels
    channels = [0] * 8
    
    # channel: 11 bit
    # data: 8 bit
    # 0x07FF is 0b11111111111 or 0000 0111 1111 1111
    
    # channel[0] takes 8 bits (all) from data[0] and then shift data[1] left by 8
    # this gives 16 bits which is masked to 11 with & 0x07FF
    channels[0] = (data[0] | (data[1] << 8)) & 0x07FF
    
    # channel[0] used 3 bits from data[1] so shift that right by 3 to get the remaining 5 bits
    # then shift data[2] by 5 to get correct bits (6 used from data[2])
    channels[1] = (data[1] >> 3 | data[2] << 5) & 0x07FF
    
    # channel[1] used 6 bits from data[2] which was shifted 5 left so shift it back 6 right to get the remaining 2
    # then combine this with 8 bits from data 3 and 1 from data 4 to make 11
    channels[2] = ((data[2] >> 6) | (data[3] << 2) | (data[4] << 10)) & 0x07FF
    
    # 1 bit of data 4 was used so shift right by 1 then combine with data 5
    channels[3] = (data[4] >> 1 | data[5] << 7) & 0x07FF
    
    # im not explaining the rest which are for switches which are the same
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

last_signal_strength = 0
last_signal_quality = 0

while True:
    # if there is any recieved data
    if uart0.any():
        # read the data
        raw_data = uart0.read()
        data_length = len(raw_data)
        
        for i in range(len(raw_data) - 2):
            
            if raw_data[i] == 0x16:
                if i + 22 <= data_length:
                    # control stuff
                    # cut off header and sync
                    payload = raw_data[i:]
                    
                    # channels for my controller at least:
                    # joysticks: (range: 174 - 1811):
                    # 0 - right joystick x
                    # 1 - right joystick y
                    # 2 - left joystick y
                    # 3 - left joystick x
                    # switches are left to right for me on my controller and I only have 4
                    channels = decode(payload)
                    
                    print(f'Joysticks (x, y): ({channels[3]}, {channels[2]}), ({channels[0]}, {channels[1]})')
                    print(f'Switches:         [{channels[4]}], [{channels[5]}], [{channels[6]}], [{channels[7]}]')
                    print(f'signal data: {last_signal_strength}dbm, {last_signal_quality}%')
                    continue

            elif raw_data[i] == 0x14:
                if i + 10 <= data_length:
                    # signal quality stuff
                    payload = raw_data[i:]
                    stats = decode_signal_data(payload)
                    last_signal_strength = stats['rssi1']
                    last_signal_quality = stats['lq']
                    continue

    time.sleep(0.1)