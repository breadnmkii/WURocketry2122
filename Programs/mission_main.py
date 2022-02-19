import os
import time
import datetime

# Board
import board
import busio
import RPi.GPIO as GPIO
from digitalio import DigitalInOut

# GPIO Setup (6th Top-right pin is GPIO18)
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(18,GPIO.OUT)
GPIO.output(18,GPIO.LOW)

# Adafruit libraries
import adafruit_gps
import adafruit_bno055
import adafruit_rfm9x

# External file imports
import position as pos  # IMU tracking
import grid             # Gridding

def acquire_gps(gps):
    while not gps.has_fix:
        gps.update()
    return (gps.latitude, gps.longitude)

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

def transmit_rf(rfm9x, string):
    tx_data = bytes(string, 'utf-8')
    rfm9x.send(tx_data)


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
    FREQ = 433.0
    CS = DigitalInOut(board.CE1)
    RESET = DigitalInOut(board.D25)
    spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
    rfm9x = setup_rf(spi, CS, RESET, FREQ)



    # Initial GPS acquisition routine
    print("Acquiring GPS fix...")
    acquire_gps(gps)
    print(f"Acquired.")
    
    # IMU calibration routine
    print("Calibrating IMU...")
    calibrate_imu(imu)
    print("Calibrated!")
    

    # Declarations
    time_lastSample = time.time()
    FREQUENCY = 1/100                # (in seconds)

    hasLaunched = False              # Boolean that indicates initial rapid acceleration was detected (launched)
    hasLanded   = False              # Boolean that indicates no acceleration IF hasLaunched is true  (landed)

    acc_accumulator  = []            # List that accumulates acceleration values to apply a rolling mean
    motionless_count = 0             # Counter for number of cycles where no motion is detected, resets on movement (determines landing)

    ACC_WINDOW = 50                  # Range of values to apply rolling average in 'acc_accumulator'
    MIN_IMU_TIME = 0.5               # (seconds) Minimum time IMU should collect data to prevent immediate landing event detection
    MOTION_SENSITIVITY = 3           # Amount of 3-axis acceleration needed to be read to trigger "movement" detection
    MOTION_LAUNCH_SENSITIVITY = 12   # Amount of accel added to offset for stronger initial launch accel
    LANDED_COUNT = 10*(1/FREQUENCY)  # Number of cycles needed to be exceeded to mark as landed

    acc_data = []   # 2d array
    qua_data = []   # 2d array
    time_data = []  # 1d array

    # File IO setup
    PATH_BLACKBOX = "blackbox.log"
    if(not os.path.isfile(f"{PATH_BLACKBOX}")):
        data_f = open(f"{PATH_BLACKBOX}", "w+")
    data_f = open(f"{PATH_BLACKBOX}", "w+")

    transmit_rf(rfm9x, "SETUP")



    ### PRE-LAUNCH STANDBY ###
    print("Waiting for launch...")
    while(not hasLaunched):
        time_thisSample = time.time()
        if(time_thisSample - time_lastSample >= FREQUENCY):
            time_lastSample = time_thisSample
            acc = imu.linear_acceleration

            # Guard against None values
            if(acc[0]):
                acc_accumulator.append(sum(acc))
            
        # Take average of latest 'ACC_WINDOW' elements of 'acc_accumulator' and check if above movement_threshold
        if(average_window(acc_accumulator, ACC_WINDOW) > MOTION_SENSITIVITY + MOTION_LAUNCH_SENSITIVITY):
            print("Launch detected!")
            LAUNCH_COORD = acquire_gps(gps)
            current_coord = LAUNCH_COORD
            current_grid = (0,0)
            expected_grid = (0,0)
            hasLaunched = True
            break

    transmit_rf(rfm9x, "LAUNCH")


    ### IN-FLIGHT DATA COLLECTION ###
    print("Watiting for landing...")
    acc_accumulator.clear()
    time_launchStart = time.time()  # Marks time at launch
    time_lastSample = time.time()   # Reset delta timing

    for i in range(0,50):
        time_thisSample = time.time()

        if(time_thisSample - time_lastSample >= FREQUENCY):
            time_lastSample = time_thisSample

            acc = (1,1,1) #imu.linear_acceleration
            qua = (0,0,0,1) #imu.quaternion

            # Blackbox recording (ACCx,y,z QUAx,y,z)
            data_f.write(f"{time_thisSample-time_launchStart}")
            data_f.write(f"{acc[0]}\t{acc[1]}\t{acc[2]}\t")
            data_f.write(f"{qua[0]}\t{qua[1]}\t{qua[2]}\n")

            # Data recording
            time_data.append(time_thisSample-time_launchStart)
            acc_data.append(acc)
            qua_data.append(qua)
            

            if(acc[0] is not None and qua[0] is not None):
                acc_accumulator.append(sum(acc))
            print(motionless_count)
            # Check after some duration post launch for no motion (below movement_threshold)
            if((time_thisSample - time_launchStart >= MIN_IMU_TIME) and average_window(acc_accumulator, ACC_WINDOW) < MOTION_SENSITIVITY):
                motionless_count += 1
            else:
                motionless_count = 0    # Reset on motion detection
            print(f'{motionless_count}\n')

            if(motionless_count >= LANDED_COUNT):
                print("Landing detected!")
                print(f"Launch duration:{time_thisSample-time_launchStart}")
                hasLanded = True
                break

    # transmit_rf(rfm9x, "LANDED\n")
    data_f.close()

    ### POST-FLIGHT CALCULATION ###
    # Calculate final position
    # Notes: Uses post processing of data
    # 1. replace any NONE readings with average of points in between
    # 2. assert no NONE values exist in data
    # 3. feed data into post_track.py
    # 4. read last value of pos data
    # 5. feed pos data into grid.py
    # 6. obtain final values,
    final_position = pos.acc_to_pos(acc_data, qua_data, time_data)

    # Calculate grid number
    grid_num = grid.dist_to_grid(final_position)
    str_grid = f'{grid_num[0]},{grid_num[1]}\r\n'
    
    # Save data
    print("Saved data to file!")
    with open("grid_number.txt", "w+") as file:
        file.write(str_grid)
    
    with open("final_position.txt", "w+") as file:
        file.write(final_position)

    # Transmit data
    print("Send signal loop...")
    while True:
        transmit_rf(rfm9x, f"KEY:{str_grid}")

if __name__ == '__main__':
    main()
