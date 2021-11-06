# Main file for tracking program
import time
import board
import busio

# External file imports
import position

import adafruit_gps
import adafruit_bno055

i2c = board.I2C()

# GPS Config
gps = adafruit_gps.GPS_GtopI2C(i2c, debug=False)
gps.send_command(b"PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0")
gps.send_command(b"PMTK220,1000")
# IMU Config
imu = adafruit_bno055.BNO055_I2C(i2c)

# Initial GPS acquisition routine
print("Waiting for GPS fix...")
while not gps.has_fix:
    gps.update()
LAUNCH_COORD = (gps.latitude, gps.longitude)
print(f"Obtained launch coordinates: {LAUNCH_COORD}")


# Main payload routine
def main():
    # Two dimensional vectors
    current_coord = (0,0)
    current_grid = (0,0)
    current_acceleration = (0,0)
    current_velocity = (0,0)
    launch_displacement = (0,0)
    last_sample = time.monotonic()
    
    while True:
        # Delta timing
        this_sample = time.monotonic()
        if this_sample - last_sample >= 1.0:
            last_sample = this_sample
            ## Sample devices ##
            print('\n')
            # GPS
            if gps.has_fix:
                current_coord = (gps.latitude, gps.longitude)
                print(f'Current coordinates: {current_coord}\n')
            
            # IMU
            current_acceleration = imu.acceleration[:1]
            print(f'Current acceleration:{current_acceleration}\n')
            current_velocity = position.integrate_laccel(current_acceleration)
            print(f'Current velocity:    {current_velocity}\n')
            launch_displacement = position.update_disp(current_velocity)
            print(f'Launch displacement: {launch_displacement}')


            # RF


            ## Simple test routines ##
            # Test GPS coordinates to grid number
            current_grid = position.dist_to_grid(position.coord_to_dist(LAUNCH_COORD, current_coord))
            print(f'Current grid:{current_grid}\n')

if __name__ == '__main__':
    main()