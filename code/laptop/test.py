import cv2
import tkinter as tk
from PIL import Image, ImageTk

# Initialize main window
root = tk.Tk()
root.title("Dashcam Viewer")

# Create a label to show the video
lmain = tk.Label(root)
lmain.pack()

# Open dashcam stream (replace 0 with device index or stream URL)
cap = cv2.VideoCapture(0)

def video_stream():
    ret, frame = cap.read()
    if ret:
        # OpenCV reads BGR, Tkinter/PIL needs RGB
        cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(cv2image)
        imgtk = ImageTk.PhotoImage(image=img)
        
        # Prevent garbage collection by keeping a reference
        lmain.imgtk = imgtk
        lmain.configure(image=imgtk)
        
    # Repeat every 15 milliseconds
    lmain.after(15, video_stream)

# Run the stream loop
video_stream()
root.mainloop()
