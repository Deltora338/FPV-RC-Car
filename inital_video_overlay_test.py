import cv2
import serial

def decode_signal_data(payload):  # type: ignore
    # dBm
    uplink_rssi1 = -payload[1]  # type: ignore
    uplink_rssi2 = -payload[2]   # type: ignore
    link_quality = payload[3]    # type: ignore
    
    return {
        "rssi1": uplink_rssi1,  # type: ignore
        "rssi2": uplink_rssi2,
        "lq": link_quality
    }

# Initialize webcam (0 is usually the default built-in camera)
cap = cv2.VideoCapture(0)
try:
    ser = serial.Serial('COM10', 420000, timeout=1)
    com = True
except Exception as e:
    print(e)
    com = False

telemetry_string = "No COM port connected"

if not cap.isOpened():
    print("Error: Could not open webcam.")
    exit()

print("Press 'q' to quit the video stream.")

last_signal_strength = 0
last_signal_quality = 0

buf = bytearray()

while True:
    # 1. Read a frame from the webcam
    ret, frame = cap.read()
    if not ret:
        print("Error: Can't receive frame.")
        break

    # Drain whatever is available and append to buffer
    if com:
        waiting = ser.in_waiting  # type: ignore
        if waiting:
            buf += ser.read(waiting)  # type: ignore
        
        # Process all complete frames in the buffer
        i = 0
        channels = [0] * 8  # Initialize channels to avoid reference before assignment

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
        
            if frame_type == 0x14 and len(payload) >= 4:
                stats = decode_signal_data(payload)
                last_signal_strength = stats['rssi1']
                last_signal_quality = stats['lq']
            
            i += total_frame
        telemetry_string = f"Signal: {last_signal_strength}dBm, {last_signal_quality}%"

        # 3. Overlay the telemetry onto the frame
        # cv2.putText parameters: (image, text, position (x,y), font, font_scale, color (BGR), thickness)
    cv2.putText(
        img=frame,
        text=telemetry_string,
        org=(20, 40),  # Coordinates of the bottom-left corner of the text
        fontFace=cv2.FONT_HERSHEY_SIMPLEX,
        fontScale=0.7,
        color=(0, 255, 0),  # Bright green in BGR
        thickness=2,
        lineType=cv2.LINE_AA
    )

    # 4. Display the resulting frame
    cv2.imshow('Telemetry Overlay Feed', frame)

    if cv2.getWindowProperty('Telemetry Overlay Feed', cv2.WND_PROP_VISIBLE) < 1:
        break

# Clean up and close windows
cap.release()
cv2.destroyAllWindows()