from machine import UART, Pin
import time

# UART1: TX=GP4, RX=GP5
gps = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))

def parse_gngga(sentence):
    """Parse a $GNGGA sentence for position and fix info."""
    parts = sentence.split(',')
    if len(parts) < 10:
        return None
    try:
        time_utc = parts[1]
        lat_raw  = parts[2]; lat_dir = parts[3]
        lon_raw  = parts[4]; lon_dir = parts[5]
        fix      = int(parts[6])   # 0=no fix, 1=GPS, 2=DGPS
        sats     = parts[7]
        alt      = parts[9]

        if not lat_raw or fix == 0:
            return None

        # Convert NMEA ddmm.mmmm → decimal degrees
        lat_deg = float(lat_raw[:2]) + float(lat_raw[2:]) / 60
        lon_deg = float(lon_raw[:3]) + float(lon_raw[3:]) / 60
        if lat_dir == 'S': lat_deg = -lat_deg
        if lon_dir == 'W': lon_deg = -lon_deg

        return {
            'time': time_utc,
            'lat':  lat_deg,
            'lon':  lon_deg,
            'fix':  fix,
            'sats': sats,
            'alt':  alt,
        }
    except (ValueError, IndexError):
        return None

buf = b''

while True:
    if gps.any():
        buf += gps.read(gps.any())
        while b'\n' in buf:
            line, buf = buf.split(b'\n', 1)
            sentence = line.decode('ascii', 'ignore').strip()

            if sentence.startswith('$GNGGA') or sentence.startswith('$GPGGA'):
                data = parse_gngga(sentence)
                if data:
                    print(f"Fix: {data['fix']}  Sats: {data['sats']}")
                    print(f"Lat: {data['lat']:.6f}  Lon: {data['lon']:.6f}")
                    print(f"Alt: {data['alt']}m  Time: {data['time']}")
                else:
                    print("No fix yet...")

            elif sentence.startswith('$GNRMC') or sentence.startswith('$GPRMC'):
                # Also useful: contains speed and heading
                print("RMC:", sentence)

    time.sleep_ms(100)