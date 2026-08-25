import cv2
import serial
import time
import json
import tkinter as tk
import queue
import threading
from tkinter import messagebox
from PIL import Image, ImageTk
from typing import Any

start_time = time.time()

def read_telemetry(ser: serial.Serial | None) -> dict[str, str | int] | None:
    """Reads incoming telemetry data from the car and returns it as a dictionary"""
    if ser is None:
        return {"voltage" : "--V",
                "camera allowance" : 180,
                "camera cooldown" : 0,
                "elrs " : '-x dbm',
                "error logs" : "--",
                "uptime" : int(time.time() - start_time),
                "armed" : False
                }

    if ser.in_waiting:
        line = ser.readline()  # reads until \n or timeout
        if not line:
            return None
        try:
            data_str = line.decode('utf-8').strip() 
            if not data_str:
                return None
            try:
                with open("data_logs.txt", 'x') as file:
                    file.write(f'{data_str}\n')
            except FileExistsError:
                with open("data_logs.txt", 'a') as file:
                    file.write(f'{data_str}\n')

            return json.loads(data_str)
        except (UnicodeDecodeError, json.JSONDecodeError):
            return None
    return None


def find_available_cameras(max_tested: int=5) -> list[int]:
    """Checks for any/all available cameras that can be accessed by OpenCV and returns a list of their indexes"""
    available_cameras: list[int] = []
    
    for index in range(max_tested):

        # create a camera object with the index
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


class Window:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Camera selection Viewer")

        self.cap: cv2.VideoCapture | None = None
        self._after_id: str | None = None

        try:
            self.ser = serial.Serial("COM15", 57600, timeout=1)  # Adjust COM port and baud rate as needed
        except serial.SerialException:
            self.ser = None

        self.cameras_radiobuttons: list[tk.Radiobutton] = []
        self.selected_camera_index = tk.IntVar(value=-1)  # Default to 0 (usually built in camera)

        self.image = tk.Label(self.root)
        self.image.grid(row=0, column=1, rowspan=10)

        for index in find_available_cameras():
            rb = tk.Radiobutton(self.root, text=f"Camera {index + 1}", variable=self.selected_camera_index, value=index, command=lambda idx=index: self.on_camera_button_selected(idx), font=("Times", 12))
            rb.grid(row=index, column=0, sticky=tk.W, padx=10, pady=10)
            self.cameras_radiobuttons.append(rb)

        self.telemetry_queue: Any = queue.Queue()
        self.telemetry: dict[str, str | int] | None = {}          # latest known values
        self.last_telemetry_time = 0

        self._stop_event = threading.Event()
        self._telemetry_thread = threading.Thread(
            target=self._telemetry_worker, daemon=True
        )
        self._telemetry_thread.start()

        self.poll_telemetry()  # start draining the queue on the GUI thread

        self.fpv_button = tk.Button(
        self.root, text="Launch dedicated\nFPV window", command=self.launch_fpv_view)
        self.fpv_button.grid(row=len(self.cameras_radiobuttons), column=0, sticky=tk.W, pady=10, padx=10)

    def launch_fpv_view(self):
        # 1. Cancel ongoing Tkinter video frame updates
        if self._after_id is not None:
            self.image.after_cancel(self._after_id)
            self._after_id = None

        if self.cap is None or not self.cap.isOpened():
            messagebox.showerror("No camera", "Select a camera first")
            return

        # 2. Store camera index and release Tkinter capture
        camera_idx = self.selected_camera_index.get()
        self.cap.release()
        self.cap = None

        self.root.destroy()  # Destroy Tkinter window

        # Small delay to allow camera hardware to reset handles
        time.sleep(0.2)

        # Re-open camera for OpenCV window
        fresh_cap = cv2.VideoCapture(camera_idx, cv2.CAP_DSHOW)
        
        # Ensure camera opens properly
        if not fresh_cap.isOpened():
            print("[ERROR] Could not reopen camera for FPV view.")
            return

        self._run_opencv_view(fresh_cap)

    def _run_opencv_view(self, cap: cv2.VideoCapture):
        window_name = "FPV Feed"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

        while cap.isOpened():
            if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                break

            ret, frame = cap.read()

            # Ensure valid frame before running telemetry or displaying
            if not ret or frame is None or frame.size == 0 or frame.shape[0] == 0 or frame.shape[1] == 0:
                time.sleep(0.01)
                continue

            self._drain_telemetry_queue()
            frame = self.draw_overlay(frame)

            # Double-check frame integrity before passing to imshow
            if frame is not None and frame.shape[0] > 0 and frame.shape[1] > 0:
                cv2.imshow(window_name, frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self._stop_event.set()
        cap.release()
        cv2.destroyAllWindows()

    
    def _telemetry_worker(self):
        while not self._stop_event.is_set():
            data = read_telemetry(self.ser)
            if data is not None:
                self.telemetry_queue.put(data)
            time.sleep(0.5 if self.ser is None else 0.02)

    def poll_telemetry(self):
        # Drains whatever's arrived since the last poll — never blocks.
        try:
            while True:
                data = self.telemetry_queue.get_nowait()
                self.telemetry.update(data)
                self.last_telemetry_time = time.time()
        except queue.Empty:
            pass
        self.root.after(50, self.poll_telemetry)  # telemetry doesn't need 15ms cadence

    def on_camera_button_selected(self, index: int):
        if self._after_id is not None:
            self.image.after_cancel(self._after_id)
            self._after_id = None

        if self.cap is not None:
            self.cap.release()

        for i, rb in enumerate(self.cameras_radiobuttons):
            rb.config(bg="lightblue" if i == index else "SystemButtonFace")

        self.cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)

        # DSHOW can report isOpened() True before the device is actually
        # ready to deliver a frame — give it a couple of tries.
        ok = False
        for _ in range(5):
            if self.cap.isOpened():
                ok, _ = self.cap.read()
                if ok:
                    break
            time.sleep(0.1)

        if not ok:
            messagebox.showerror("Camera error", f"Could not open camera {index}")
            self.cap.release()
            self.cap = None
            return

        self.video_frame()

    def video_frame(self):
        if self.cap is None or not self.cap.isOpened():
            return

        ret, frame = self.cap.read()
        if ret:
            stale = (time.time() - self.last_telemetry_time) > 2.0
            colour = (0, 0, 255) if stale else (0, 255, 0)  # BGR — red if link is dead


            locations = [(10,470), (10,25), (355,470), (200,470), (10,52), (190,25), (440,25), (10,77)]

            if self.telemetry is None:
                stale = True
            
            telem = [
                f"Battery: 12.2V",
                f"Armed: {self.telemetry.get('armed', '--')}",
                f"ELRS connection: {self.telemetry.get('elrs ', '--dbm')}",
                f"Uptime: {self.telemetry.get('uptime', '--')}",
                f"Error log: {self.telemetry.get('error logs', '--')}",
                f"Camera allowance: {self.telemetry.get('camera allowance', '--')},",
                f" Cooldown: {self.telemetry.get('camera cooldown', '--')}",
                "NO TELEMETRY" if stale else 'LINK OK',
            ]

            for i, info in enumerate(telem):
                cv2.putText(frame, str(info), locations[i], cv2.FONT_HERSHEY_SIMPLEX,
                            0.6, colour, 2, cv2.LINE_AA)

            cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(cv2image)
            imgtk = ImageTk.PhotoImage(image=img)
            self.image.imgtk = imgtk
            self.image.configure(image=imgtk)

        self._after_id = self.image.after(15, self.video_frame)

    def _drain_telemetry_queue(self):
        try:
            while True:
                data = self.telemetry_queue.get_nowait()
                self.telemetry.update(data)
                self.last_telemetry_time = time.time()
        except (queue.Empty, Exception):
            pass


    def draw_overlay(self, frame):
        """Takes current telemetry and writes it over the current frame"""
        if frame is None or frame.size == 0:
            return frame

        stale = (time.time() - self.last_telemetry_time) > 2.0
        colour = (0, 0, 255) if stale else (0, 255, 0)

        locations = [(10, 470), (10, 25), (355, 470), (200, 470), (10, 52), (190, 25), (440, 25), (10, 77)]

        telem = [
            "Battery: 12.2V",
            f"Armed: {self.telemetry.get('armed', '--')}",
            f"ELRS connection: {self.telemetry.get('elrs ', '--dbm')}",
            f"Uptime: {self.telemetry.get('uptime', '--')}",
            f"Error log: {self.telemetry.get('error logs', '--')}",
            f"Camera allowance: {self.telemetry.get('camera allowance', '--')}",
            f"Cooldown: {self.telemetry.get('camera cooldown', '--')}",
            "NO TELEMETRY" if stale else "LINK OK",
        ]

        for i, info in enumerate(telem):
            if i < len(locations):
                cv2.putText(
                    frame,
                    str(info),
                    locations[i],
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    colour,
                    2,
                    cv2.LINE_AA
                )

        return frame




if __name__ == "__main__":
    window = Window()
    window.root.mainloop()
