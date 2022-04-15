import os
import time
import datetime

# SciKit Kinematics IMU Tracking
from skinematics.imus import IMU_Base
from scipy.spatial.transform import Rotation as R
import pandas as pd

# Board
import board
import busio
import RPi.GPIO as GPIO
from digitalio import DigitalInOut

# Adafruit libraries
import adafruit_gps
import adafruit_bno055
import adafruit_rfm9x

# External file imports
import position as pos  # IMU tracking
import average as avg   # Averaging/Noise Filter
import grid             # Gridding

# GPIO Setup (6th Top-right pin is GPIO18)
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(17,GPIO.OUT)
GPIO.setup(18,GPIO.OUT)

# Output LOW
GPIO.output(17,GPIO.LOW)
GPIO.output(18,GPIO.LOW)

################################################################################################################################################################
# Helper functions
def acquire_gps(gps, timeout):
    timecount = 0
    while not gps.has_fix:
        gps.update()
        timecount += 1
        if(timecount >= timeout):
            return None
    return (gps.latitude, gps.longitude)


def calibrate_gps(gps):
    if(acquire_gps(gps, 300)):
        GPIO.output(17,GPIO.HIGH)
        print(f"Acquired.")
    else:
        GPIO.output(17,GPIO.LOW)
        print(f"Did not acquire. Retry if necessary.")


def calibrate_imu(imu):
    while(imu.calibration_status[1] != 3 or imu.calibration_status[2] != 3):
        pass
    GPIO.output(18,GPIO.HIGH)   # Signal is calibrated


def average_window(list, window):
    if(not list):
        return 0
    return sum(map(lambda acc: abs(acc), list[-window:]))/window


def setup_rf(spi, CS, RESET, FREQ):
    while True:
        # Attempt setting up RFM9x Module
        try:
            rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, FREQ)
            rfm9x.tx_power = 23
            print('RFM9x SET\n')
            return rfm9x

        except RuntimeError as error:
            print('RFM9 ERR: Check wiring\n')

def transmit_rf(rfm9x, string, count=1):
    while count > 0:
        tx_data = bytes(string, 'utf-8')
        rfm9x.send(tx_data)
        count -= 1

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
        data = pd.read_csv(in_file,
                           sep='\t',
                           index_col=False)
        rate = 100   # in Hz
    
        # Extract data from columns (Each in a 3-vector of x,y,z)
        in_data = {
            'rate':rate,
            'acc':   data.filter(regex='Acc').values,
            'omega': data.filter(regex='Gyr').values}

        self._set_data(in_data)

################################################################################################################################################################
################################################################################################################################################################
# Main payload routine
def main():
    i2c = board.I2C()

    # GPS
    gps = adafruit_gps.GPS_GtopI2C(i2c, debug=False)
    gps.send_command(b"PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0")
    gps.send_command(b"PMTK220,1000")

    # IMU
    imu = adafruit_bno055.BNO055_I2C(i2c)
    imu.mode = adafruit_bno055.IMUPLUS_MODE     # NO MAGNETOMETER MODE
    imu.accel_range = adafruit_bno055.ACCEL_16G

    # RF
    # Configure radio frequencies
    rf_channel = 7
    rf_freq = 434.550 + rf_channel * 0.1
    CS = DigitalInOut(board.CE1)
    RESET = DigitalInOut(board.D25)
    spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
    rfm9x = setup_rf(spi, CS, RESET, rf_freq)

    # Attempt GPS acquisition routine
    print("Acquiring GPS fix...")
    calibrate_gps(gps)
    
    # IMU calibration routine
    print("Calibrating IMU...")
    calibrate_imu(imu)
    print("Calibrated!")

    # Declarations
    time_lastSample = time.time()
    SAMPLE_FREQ = 1/100                # (in seconds)

    hasLaunched = False              # Boolean that indicates initial rapid acceleration was detected (launched)
    hasLanded   = False              # Boolean that indicates no acceleration IF hasLaunched is true  (landed)

    acc_accumulator  = []            # List that accumulates acceleration values to apply a rolling mean
    motionless_count = 0             # Counter for number of cycles where no motion is detected, resets on movement (determines landing)

    ACC_WINDOW = 50                  # Range of values to apply rolling average in 'acc_accumulator'
    MIN_IMU_TIME = 0.5               # (seconds) Minimum time IMU should collect data to prevent immediate landing event detection
    MOTION_SENSITIVITY = 3           # Amount of 3-axis acceleration needed to be read to trigger "movement" detection
    MOTION_LAUNCH_SENSITIVITY = 13   # Amount of accel added to offset for stronger initial launch accel
    LANDED_COUNT = 10*(1/SAMPLE_FREQ)  # Number of cycles needed to be exceeded to mark as landed

    acc_data = []   # 2d array
    qua_data = []   # 2d array
    time_data = []  # 1d array

    # # Scikit Tracking Data Container
    data = {"Acc_X":[],
            "Acc_Y":[],
            "Acc_Z":[],
            "Gyr_X":[],
            "Gyr_Y":[],
            "Gyr_Z":[]}

    transmit_rf(rfm9x, "SETUP: Done", count=30)

    ################################################################################################################################################################
    ### PRE-LAUNCH STANDBY ###
    print("Waiting for launch...")
    while(not hasLaunched):

        # Acceleration sampling for motion detection
        time_thisSample = time.time()
        if(time_thisSample - time_lastSample >= SAMPLE_FREQ):
            time_lastSample = time_thisSample
            acc = imu.linear_acceleration
            if(None not in acc):
                acc_accumulator.append(sum(acc))
            
        # Take average of latest 'ACC_WINDOW' elements of 'acc_accumulator' and check if above movement_threshold
        if(average_window(acc_accumulator, ACC_WINDOW) > MOTION_SENSITIVITY + MOTION_LAUNCH_SENSITIVITY):
            print("Launch detected!")
            LAUNCH_COORD = acquire_gps(gps, 10)
            hasLaunched = True

            # Obtain initial launch orientation
            quat = imu.quaternion                        # [w,x,y,z]   scalar first format (Bosch + Skin convention)
            formatted_quat = (*(quat[1:]), quat[0])
            init_orient = R.from_quat(formatted_quat).as_matrix()  # [x,y,z]+[w] scalar last format (Scipy convention)
            break
    
    transmit_rf(rfm9x, "LAUNCH")


    ################################################################################################################################################################
    ### IN-FLIGHT DATA COLLECTION ###
    print("Watiting for landing...")
    acc_accumulator.clear()
    time_launchStart = time.time()  # Marks time at launch
    time_lastSample = time.time()   # Reset delta timing

    while(not hasLanded):
        time_thisSample = time.time()

        # Flight data sampling
        if(time_thisSample - time_lastSample >= SAMPLE_FREQ):
            time_lastSample = time_thisSample

            acc = imu.linear_acceleration
            omg = imu.gyro

            if(None not in acc and None not in omg):
                acc_accumulator.append(sum(acc))

                data["Acc_X"].append(acc[0])
                data["Acc_Y"].append(acc[1])
                data["Acc_Z"].append(acc[2])
                data["Gyr_X"].append(omg[0])
                data["Gyr_Y"].append(omg[1])
                data["Gyr_Z"].append(omg[2])
            
            
            # Check after some duration post launch for no motion (below movement_threshold)
            if((time_thisSample - time_launchStart >= MIN_IMU_TIME) and average_window(acc_accumulator, ACC_WINDOW) < MOTION_SENSITIVITY):
                motionless_count += 1
            else:
                motionless_count = 0    # Reset on motion detection

            transmit_rf(rfm9x, "CHECK: Flying")

            if(motionless_count >= LANDED_COUNT):
                print("Landing detected!")
                print(f"Launch duration:{time_thisSample-time_launchStart}")
                hasLanded = True
                break


    ################################################################################################################################################################
    ### POST-FLIGHT CALCULATION ###
    transmit_rf(rfm9x, "LANDED\n", count=30)

    ## Scikit Position Track
    df = pd.DataFrame(data, index=None)
    df.to_csv('blackbox.txt', index=None, sep="\t", mode="w")
    mySensor = XSens(in_file='blackbox.txt', R_init=init_orient)
    position_matrix = mySensor.calc_position()

    # Calculate grid number
    grid_num = grid.calculate_grid(LAUNCH_COORD, position_matrix[-1])
    expected_num = grid.dist_to_grind(grid.dist_between_coord(LAUNCH_COORD, acquire_gps(gps, 20)))
    str_grid = f'{grid_num}\r\n'
    
    # Save grid data
    with open("grid_number.txt", "w+") as file:
        file.write(str_grid)
        file.close()

    with open("final_position.txt", "w+") as file:
        file.write(f"{position_matrix[-1][0]},{position_matrix[-1][1]}")
        file.close()

    # Transmit data
    print("Send signal loop...")
    while True:
        transmit_rf(rfm9x, f"KEY:{str_grid}")
        transmit_rf(rfm9x, f"Expected Grid: ")

if __name__ == '__main__':
    main()