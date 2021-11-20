# Main file for tracking program
import time
import board
import busio
from digitalio import DigitalInOut

# Adafruit libraries
import adafruit_gps
import adafruit_bno055
import adafruit_rfm9x

# External file imports
import position as pos  # IMU tracking
import grid             # Gridding


i2c = board.I2C()

# GPS Config
gps = adafruit_gps.GPS_GtopI2C(i2c, debug=False)
gps.send_command(b"PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0")
gps.send_command(b"PMTK220,1000")

# IMU Config
imu = adafruit_bno055.BNO055_I2C(i2c)
# imu.mode = adafruit_bno055.IMUPLUS_MODE     # NO MAGNETOMETER MODE

# RF Config
CS = DigitalInOut(board.CE1)
RESET = DigitalInOut(board.D25)
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)

# Initial GPS acquisition routine
print("Waiting for GPS fix...")
while not gps.has_fix:
   gps.update()
LAUNCH_COORD = (gps.latitude, gps.longitude)

# LAUNCH_COORD = (38.663484, -90.365707)    # Debug test coordinate

print(f"Obtained launch coordinates: {LAUNCH_COORD}")


# Main payload routine
def main():
    # Two dimensional vectors
    current_coord = LAUNCH_COORD    # TODO: let current_coord be GPS coord
    current_grid = (0,0)
    expected_grid = (0,0)
    

    ### Real Time Position Tracking Process ###  (Discontinued for now)
    '''
    current_acceleration = [0,0]
    #current_velocity = [0,0]
    launch_displacement = [0,0]
    last_sample = time.monotonic()
    
    while True:
        # Delta timing
        this_sample = time.monotonic()
        sample_intv = 0.1
        if this_sample - last_sample >= sample_intv:
            
            ## Sample devices ##
            print('\n')
            # GPS
            if gps.has_fix:
                current_coord = (gps.latitude, gps.longitude)
            print(f'Current coordinates: {current_coord}\n')
            
            # IMU
            acc = imu.linear_acceleration
            # heading, roll, pitch = imu.read_euler()  # Some other library provides this orientation?
            # print(f'Heading:{heading}   Roll:{roll}   Pitch{pitch}\n')
            current_acceleration = [0. if (acc[0] is None or abs(acc[0]) < acc_lowFilter) else acc[0], 
                                    0. if (acc[1] is None or abs(acc[1]) < acc_lowFilter) else acc[1]]

            print(f'Current acceleration:{current_acceleration}\n')
            #current_velocity[0] = current_velocity[0] + temp_vel[0]
            #current_velocity[1] = current_velocity[1] + temp_vel[1]
            #print(f'Current velocity:    {tuple(current_velocity)}\n')
            temp_displacement = position.integrate_laccel(sample_intv, current_acceleration)
            launch_displacement[0] += temp_displacement[0]
            launch_displacement[1] += temp_displacement[1]
            print(f'Launch displacement: {tuple(launch_displacement)}\n')


            # RF


            ## Simple test routines ##
            # Test GPS coordinates to grid number
            current_grid = position.dist_to_grid(launch_displacement)
        
            expected_grid = position.dist_to_grid(position.coord_to_dist(LAUNCH_COORD, current_coord))
            print(f'Guess grid: {current_grid}\n')
            print(f'Actual grid:{expected_grid}\n')
            
            last_sample = this_sample
    '''
    
    ### Post-Process Position Tracking ###
    last_sample = time.time()
    frequency = 1/100           # (in seconds)

    hasLaunched = False          # Boolean that indicates initial rapid acceleration was detected (launched)
    hasLanded   = False          # Boolean that indicates no acceleration IF hasLaunched is true  (landed)

    acc_accumulator  = []        # List containing all acceleration values to apply a rolling mean
    window           = 50
    MOTION_THRESHOLD = 0.9      # Amount of 3-axis acceleration needed to be read to trigger "movement" detection
    motionless_count = 0         # Counter for number of cycles where no motion is detected, resets on movement (determines landing)
    LANDED_COUNT     = 10*(1/frequency) # Number of cycles needed to be exceeded to mark as landed

    # Loop continously checks whether rocket has launched
    print("Waiting for launch...")
    while(not hasLaunched):
        this_sample = time.time()
        if(this_sample - last_sample >= frequency):
            last_sample = this_sample
            lin_accel = imu.linear_acceleration

            if(lin_accel[0]):
                acc_accumulator.append(sum(lin_accel))
        
        # Take average of latest 'window' elements of 'acc_accumulator' and check if above movement_threshold
        if(abs(sum(acc_accumulator[-window:])/window) > MOTION_THRESHOLD + 1):      # +1 for stronger accel from launch
            print("Launch detected!")
            hasLaunched = True

    acc_accumulator = []                # Accumulates LINEAR acceleration (to determine absolute movement)
   
    f = open("data.txt", "w+")
    print("Watiting for landing...")
    launch_time = time.time()      # Marks time at launch
    last_sample = launch_time           # Reset delta timing
    min_imu_time = 0.5                   # Minimum time IMU should collect data (prevents immediate landing event detections)
    # Loop continuously gathers IMU data between hasLaunched and hasLanded
    while(not hasLanded):
        this_sample = time.time()

        if(this_sample - last_sample >= frequency):
            
            last_sample = this_sample
            lin_accel = imu.linear_acceleration

            if(lin_accel[0]):
                acc_accumulator.append(sum(lin_accel))

            w = imu.gyro
            a = imu.acceleration        # Grab NON-linear acceleration for use in computation
            m = imu.magnetic            # NOTE WE CANNOT USE MAG IN REAL LAUNCH

            if(w[0] is None or a[0] is None or m[0] is None):
                continue

            f.write(f'{w[0]},{w[1]},{w[2]},')
            f.write(f'{a[0]},{a[1]},{a[2]},')
            f.write(f'{m[0]},{m[1]},{m[2]}\n')

            # Check after some duration post launch for no motion (below movement_threshold)
            if((this_sample - launch_time >= min_imu_time) and abs(sum(acc_accumulator[-window:])/window) < MOTION_THRESHOLD):
                motionless_count += 1
            else:
                motionless_count = 0    # Reset on motion detection
            
            if(motionless_count >= LANDED_COUNT):
                print("Landing detected!")
                print(f"Launch duration:{this_sample-launch_time}")
                hasLanded = True
            print(f'{motionless_count}\n')
            print(f"AcAcc:{abs(sum(acc_accumulator[-window:])/window)}")
    f.close()

    ## Process position data
    # EKF step
    tracker = pos.IMUTracker(sampling=100)
    data = pos.receive_data()    # reads IMU data from file

    print('Initializing tracker computation...')
    init_list = tracker.initialize(data)

    a_nav, orix, oriy, oriz = tracker.attitudeTrack(data, init_list)

    # Acceleration correction step
    a_nav_filtered = tracker.removeAccErr(a_nav, filter=False)
    # plot3([a_nav, a_nav_filtered])

    # ZUPT step
    v = tracker.zupt(a_nav_filtered, threshold=0.2)
    # plot3([v])

    # Integration Step
    position_data = tracker.positionTrack(a_nav_filtered, v)
    
    ## Calculate grid number
    # Grab last displacement value's (x,y) from position data
    final_position = (position_data[-1][0], position_data[-1][1]) 
    grid_num = grid.dist_to_grid(final_position)
    str_grid = f'{grid_num[0]},{grid_num[1]}\r\n'
    
    ## Save data
    print("Saved data to file!")
    f = open("landing.txt", "w+")
    f.write(str_grid)
    f.close()

    ## Send data 
    print("Send signal loop...")
    while True:
        # Attempt setting up RFM9x Module
        try:
            rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, 915.0)
            rfm9x.tx_power = 23
            print('RFM9x successfully set up!')
            
            while True:
                # TX
                tx_data = bytes(str_grid, 'utf-8')
                rfm9x.send(tx_data)

        except RuntimeError as error:
            print('Error in setting up RFM9x... check wiring.')


if __name__ == '__main__':
    main()
