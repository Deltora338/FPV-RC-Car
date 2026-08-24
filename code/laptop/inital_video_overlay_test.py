import cv2
import serial
import time

# Initialize webcam (0 is usually the default built-in camera)
# cap = cv2.VideoCapture(1)
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

try:
    ser = serial.Serial('COM16', 420000, timeout=1)
    com = True
except Exception as e:
    print(e)
    com = False

telemetry_string = ""

if not cap.isOpened():
    print("Error: Could not open webcam.")
    exit()

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
        channels = [0] * 8  # Initialize channels to avoid reference before assignment


        # 3. Overlay the telemetry onto the frame
        # cv2.putText parameters: (image, text, position (x,y), font, font_scale, color (BGR), thickness)
    
    cv2.putText(
        img=frame,
        text=telemetry_string,
        org=(20, 40),  # Coordinates of the bottom-left corner of the text
        fontFace=cv2.FONT_HERSHEY_SIMPLEX,
        fontScale=0.7,
        color=(0, 0, 255),  # Bright green in BGR
        thickness=2,
        lineType=cv2.LINE_AA
    )

    # 4. Display the resulting frame
    cv2.imshow('Telemetry Overlay Feed', frame)

    # Break the loop if 'q' key is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

    if cv2.getWindowProperty('Telemetry Overlay Feed', cv2.WND_PROP_VISIBLE) < 1:
        break

    time.sleep(0.01)

# Clean up and close windows
cap.release()
cv2.destroyAllWindows()