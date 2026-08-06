from machine import Pin, PWM, UART
from config import *
import time
import lib

camera = fpv.Camera(camera_relay_signal_pin, VTX_status_led)

while True:
    check_battery_voltage()
    check_camera_temp()
    action()
    get_control()
    action()
    arrange_telemetry()
    send_telemetry()