import cv2

def find_available_cameras(max_tested=10):
    available_cameras = []
    
    print("Scanning for available cameras... Please wait.")
    print("-" * 45)
    
    for index in range(max_tested):
        # cv2.CAP_DSHOW speeds up the scanning process significantly on Windows
        cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        
        if cap.isOpened():
            # Try to grab a frame just to be absolutely sure it's working
            is_reading, _ = cap.read()
            if is_reading:
                print(f"[SUCCESS] Camera found at index: {index}")
                available_cameras.append(index)
            else:
                print(f"[WARNING] Camera found at index {index}, but couldn't grab a frame (busy?).")
            
            # Always release the camera after testing
            cap.release()
        else:
            # Uncomment the line below if you want to see which indexes failed
            # print(f"[FAILED ] No camera found at index: {index}")
            pass

    print("-" * 45)
    return available_cameras

if __name__ == "__main__":
    cameras = find_available_cameras(max_tested=10) # 0 to 5 is usually plenty
    
    if cameras:
        print(f"Scan complete. Available indexes to use in your code: {cameras}")
    else:
        print("Scan complete. No working cameras detected. Check your USB connections!")