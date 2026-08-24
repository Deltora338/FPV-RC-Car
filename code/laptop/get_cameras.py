import cv2
import tkinter as tk

def find_available_cameras(max_tested: int=10) -> list[int]:
    available_cameras: list[int] = []
    
    for index in range(max_tested):
        # cv2.CAP_DSHOW speeds up the scanning process significantly on Windows        
        
        cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)

        if cap.isOpened():
            is_reading, _ = cap.read() # discard unneeded info
            if is_reading:
                print(f"[SUCCESS] Camera found at index: {index}")
                available_cameras.append(index)
            else:
                print(f"[WARNING] Camera found at index {index}, but couldn't grab a frame")
            
            # release the camera
            cap.release()
        else:
            pass

    return available_cameras

