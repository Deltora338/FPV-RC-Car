from machine import Pin, UART
import time

uart0 = UART(0, baudrate=9600, stop=1, rx=Pin(1), tx=Pin(0))
uart1 = UART(1, baudrate=9600, stop=1, rx=Pin(5), tx=Pin(4))

while True:
    packet = input("/>")
    
    if packet:
        uart1.write(packet.encode('utf-8'))
        time.sleep(0.1)
        
        if uart0.any():
            data = uart0.read()
            message = data.decode('utf-8')
            print(f'Packet sent: {packet}\nData recieved: {data}\nMessage Decoded from data: {message}')
        else:
            print("error 1")
    


print("exited")