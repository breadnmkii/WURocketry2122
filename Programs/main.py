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
#LAUNCH_COORD = (38.663484, -90.365707)
print(f"Obtained launch coordinates: {LAUNCH_COORD}")


# Main payload routine
def main():
    # Two dimensional vectors
    current_coord = LAUNCH_COORD
    current_grid = (0,0)
    expected_grid = (0,0)
    
    current_acceleration = (0,0)
    current_velocity = (0,0)
    launch_displacement = (0,0)
    last_sample = time.monotonic()
    
    while True:
        # Delta timing
        this_sample = time.monotonic()
        if this_sample - last_sample >= 1.0:
            
            ## Sample devices ##
            print('\n')
            # GPS
            if gps.has_fix:
                current_coord = (gps.latitude, gps.longitude)
            print(f'Current coordinates: {current_coord}\n')
            
            # IMU
            acc = imu.acceleration
            # heading, roll, pitch = imu.read_euler()  # Some other library provides this orientation?
            print(f'Heading:{heading}   Roll:{roll}   Pitch{pitch}\n')
            current_acceleration = (0. if acc[0] is None else acc[0], 
                                    0. if acc[1] is None else acc[1])
            print(f'Current acceleration:{current_acceleration}\n')
            current_velocity += position.integrate_laccel(last_sample, 
                                                          this_sample, 
                                                          current_acceleration)
            print(f'Current velocity:    {tuple(current_velocity)}\n')
            launch_displacement = position.update_disp(launch_displacement,
                                                       current_velocity)
            print(f'Launch displacement: {tuple(launch_displacement)}\n')


            # RF


            ## Simple test routines ##
            # Test GPS coordinates to grid number
            current_grid = position.dist_to_grid(launch_displacement)
            expected_grid = position.dist_to_grid(position.coord_to_dist(LAUNCH_COORD, current_coord))
            print(f'Guess grid: {current_grid}\n')
            print(f'Actual grid:{expected_grid}\n')
            
            last_sample = this_sample

if __name__ == '__main__':
    main()
