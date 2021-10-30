# Main file for tracking program
import time
import board
import busio

import position

import adafruit_gps

i2c = board.I2C()

# GPS Configuration
gps = adafruit_gps.GPS_GtopI2C(i2c, debug=False)
gps.send_command(b"PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0")
gps.send_command(b"PMTK220,1000")

# Initial GPS acquisition routine
print("Waiting for GPS fix...")
while not gps.has_fix:
    gps.update()
LAUNCH_COORD = (gps.latitude, gps.longitude)
print(f"Obtained launch coordinates: {LAUNCH_COORD}")




# Main paylaod routine
while True:
    # Sample all devices
    pass


