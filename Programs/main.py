# Main file for tracking program
import time
import numpy as np
import pandas as pd

# Board
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

# IMU_Base
from skinematics.imus import IMU_Base

class XSens(IMU_Base):
    """Concrete class based on abstract base class IMU_Base """    
    
    def get_data(self, in_file, in_data=None):
        '''Get the sampling rate, as well as the recorded data,
        and assign them to the corresponding attributes of "self".
        
        Parameters
        ----------
        in_file : string
                Filename of the data-file
        in_data : not used here
        
        Assigns
        -------
        - rate : rate
        - acc : acceleration
        - omega : angular_velocity
        - mag : mag_field_direction
        '''
        
        # Get the sampling rate from the second line in the file
        try:
            fh = open(in_file)
            fh.close()
    
        except FileNotFoundError:
            print('{0} does not exist!'.format(in_file))
            return -1

        # Read the data
        rate = 100.0    # in Hz
        data = pd.read_csv(in_file,
                           sep='\t',
                           skiprows=4, 
                           index_col=False)
    
        # Extract data from columns (Each in a 3-vector of x,y,z)
        in_data = {'rate':rate,
               'acc':   data.filter(regex='Acc').values,
               'omega': data.filter(regex='Gyr').values,
               'mag':   data.filter(regex='Mag').values}
        self._set_data(in_data)




# Main payload routine
def main():

    ### IMU setup ###
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
    # while not gps.has_fix:
    #    gps.update()
    # LAUNCH_COORD = (gps.latitude, gps.longitude)

    LAUNCH_COORD = (38.663484, -90.365707)    # Debug test coordinate

    print(f"Obtained launch coordinates: {LAUNCH_COORD}")

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
    MOTION_THRESHOLD = 1.3      # Amount of 3-axis acceleration needed to be read to trigger "movement" detection
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
   
    # f = open("data.txt", "w+")
    print("Watiting for landing...")
    launch_time = time.time()      # Marks time at launch
    last_sample = launch_time           # Reset delta timing
    min_imu_time = 0.5                   # Minimum time IMU should collect data (prevents immediate landing event detections)

    data = {"Counter":[],
            "Acc_X":[],
            "Acc_Y":[],
            "Acc_Z":[],
            "Gyr_X":[],
            "Gyr_Y":[],
            "Gyr_Z":[],
            "Mag_X":[],
            "Mag_Y":[],
            "Mag_Z":[],
            "Quat_w":[],
            "Quat_x":[],
            "Quat_y":[],
            "Quat_z":[]}
    count = 0

    # Loop continuously gathers IMU data between hasLaunched and hasLanded
    while(not hasLanded):
        this_sample = time.time()

        if(this_sample - last_sample >= frequency):
            
            last_sample = this_sample
            lin_accel = imu.linear_acceleration

            if(lin_accel[0]):
                acc_accumulator.append(sum(lin_accel))

            acc = imu.linear_acceleration
            omg = imu.gyro
            mag = imu.magnetic
            qua = imu.quaternion

            if(omg[0] is None or acc[0] is None or mag[0] is None or qua[0] is None):
                continue

            data["Counter"].append(count)
            data["Acc_X"].append(acc[0])
            data["Acc_Y"].append(acc[1])
            data["Acc_Z"].append(acc[2])
            data["Gyr_X"].append(omg[0])
            data["Gyr_Y"].append(omg[1])
            data["Gyr_Z"].append(omg[2])
            data["Mag_X"].append(mag[0])
            data["Mag_Y"].append(mag[1])
            data["Mag_Z"].append(mag[2])
            data["Qua_W"].append(qua[0])
            data["Qua_X"].append(qua[1])
            data["Qua_Y"].append(qua[2])
            data["Qua_Z"].append(qua[3])
            

            # f.write(f'{w[0]},{w[1]},{w[2]},')
            # f.write(f'{a[0]},{a[1]},{a[2]},')
            # f.write(f'{m[0]},{m[1]},{m[2]}\n')

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

            count += 1
    # f.close()

    ## Format data to file
    print("Processing data...\n")
    df = pd.DataFrame(data, index=None)
    with open("data.txt", "w") as file:
        file.write("// Start Time: 0\n// Sample rate: 100.0Hz\n// Scenario: 4.9\n// Firmware Version: 2.5.1\n")
    df.to_csv("data.txt", index=None, sep="\t", mode="a")

    bno = XSens(in_file='data.txt')
    final_position = bno.pos
    # grid_num = grid.dist_to_grid(final_position)
    # str_grid = f'{grid_num[0]},{grid_num[1]}\r\n'
    
    ## Save data
    # print("Saved data to file!")
    # with open("landing.txt", "w") as file:
    #     file.write(str_grid)
    
    # with open("displacement.txt", "w") as file:
    #     file.write(final_position)  # FIXME: Write np array
   
    
    ## Transmit data
    print(final_position)

    print("Send signal loop...")
    while True:
        # Attempt setting up RFM9x Module
        try:
            rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, 433.0)
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
