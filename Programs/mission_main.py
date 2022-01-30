import os
import time
import datetime

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

def acquire_gps(gps):
    while not gps.has_fix:
        gps.update()
    return (gps.latitude, gps.longitude)


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
    """ Peripheral Setup """
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

    # TODO: get gps coord on launch
    # Initial GPS acquisition routine
    print("Acquiring GPS fix...")
    LAUNCH_COORD = acquire_gps(gps)
    # LAUNCH_COORD = (38.663484, -90.365707)    # Debug test coordinate
    print(f"Acquired: {LAUNCH_COORD}")
    transmit_rf(rfm9x, f"LAUNCH_COORD: {LAUNCH_COORD}\n")
    
    # IMU calibration routine
    print("Calibrating IMU...")
    while(imu.calibration_status[1] != 3 or imu.calibration_status[2] != 3):
        pass
    print("Calibrated!")

    # Declarations
    current_coord = LAUNCH_COORD
    current_grid = (0,0)
    expected_grid = (0,0)
    
    time_lastSample = time.time()
    FREQUENCY = 1/100                # (in seconds)

    hasLaunched = False              # Boolean that indicates initial rapid acceleration was detected (launched)
    hasLanded   = False              # Boolean that indicates no acceleration IF hasLaunched is true  (landed)

    acc_accumulator  = []            # List that accumulates acceleration values to apply a rolling mean
    motionless_count = 0             # Counter for number of cycles where no motion is detected, resets on movement (determines landing)

    ACC_WINDOW = 50                  # Range of values to apply rolling average in 'acc_accumulator'
    MIN_IMU_TIME = 0.5               # (seconds) Minimum time IMU should collect data to prevent immediate landing event detection
    MOTION_SENSITIVITY = 3           # Amount of 3-axis acceleration needed to be read to trigger "movement" detection
    MOTION_LAUNCH_SENSITIVITY = 10 # Amount of accel added to offset for stronger initial launch accel
    LANDED_COUNT = 10*(1/FREQUENCY)  # Number of cycles needed to be exceeded to mark as landed

    # Dictionary for IMU sensor readings
    data = {"Counter":[],
        "Acc_X":[],
        "Acc_Y":[],
        "Acc_Z":[],
        "Gyr_X":[],
        "Gyr_Y":[],
        "Gyr_Z":[],
        "Quat_w":[],
        "Quat_x":[],
        "Quat_y":[],
        "Quat_z":[]}

    # File IO setup
    PATH_BLACKBOX = "files/blackbox.log"
    if(not os.path.isfile(f"{PATH_BLACKBOX}")):
        open(f"{PATH_BLACKBOX}")
    data_f = open(f"{PATH_BLACKBOX}", "w+")

    transmit_rf(rfm9x, "SETUP: DONE\nWAIT: LAUNCH\n")

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
            hasLaunched = True
            break

    transmit_rf(rfm9x, "EVENT: LAUNCH\nWAIT: LANDING\n")

    ### IN-FLIGHT DATA COLLECTION ###
    print("Watiting for landing...")
    acc_accumulator.clear()
    time_launchStart = time.time()  # Marks time at launch
    time_lastSample = time.time()   # Reset delta timing

    while(not hasLanded):
        time_thisSample = time.time()

        if(time_thisSample - time_lastSample >= FREQUENCY):
            time_lastSample = time_thisSample

            acc = imu.linear_acceleration
            qua = imu.quaternion

            if(acc[0] is not None and qua[0] is not None):
                acc_accumulator.append(sum(acc))
                data_f.write(f"ACC_X: {acc[0]}\tACC_Y: {acc[1]}\tACC_Z: {acc[2]}\n")

                # transmit_rf(rfm9x, f"\n{datetime.datetime.now()}\n")
                # transmit_rf(rfm9x, f"ACC_X: {acc[0]}\tACC_Y: {acc[1]}\tACC_Z: {acc[2]}\n")

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

    transmit_rf(rfm9x, "EVENT: LANDING\n")
    
    ### POST-FLIGHT CALCULATION ###
    # Calculate final position
    final_position = (100,100)

    # Calculate grid number
    grid_num = grid.dist_to_grid(final_position)
    str_grid = f'{grid_num[0]},{grid_num[1]}\r\n'
    
    # Save data
    print("Saved data to file!")
    with open("files/grid_number.txt", "w") as file:
        file.write(str_grid)
    
    with open("files/final_position.txt", "w") as file:
        file.write(final_position)

    # Transmit data
    print("Send signal loop...")
    while True:
        transmit_rf(rfm9x, f"KEY:{str_grid}")


if __name__ == '__main__':
    main()
