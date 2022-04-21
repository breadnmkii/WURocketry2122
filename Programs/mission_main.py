import os
import time
import datetime
from turtle import position

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

THE_COEFFICIENT = 36

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
        print(f"Acquired.")
    else:
        print(f"Did not acquire. Retry if necessary.")


def calibrate_imu(imu):
    while(imu.calibration_status[1] != 3 or imu.calibration_status[2] != 3):
        pass

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
    FREQUENCY = 1/100                # (in seconds)

    hasLaunched = False              # Boolean that indicates initial rapid acceleration was detected (launched)
    hasLanded   = False              # Boolean that indicates no acceleration IF hasLaunched is true  (landed)

    acc_accumulator  = []            # List that accumulates acceleration values to apply a rolling mean
    motionless_count = 0             # Counter for number of cycles where no motion is detected, resets on movement (determines landing)

    ACC_WINDOW = 50                  # Range of values to apply rolling average in 'acc_accumulator'
    MIN_IMU_TIME = 0.5               # (seconds) Minimum time IMU should collect data to prevent immediate landing event detection
    MOTION_SENSITIVITY = 3           # Amount of 3-axis acceleration needed to be read to trigger "movement" detection
    MOTION_LAUNCH_SENSITIVITY = 13   # Amount of accel added to offset for stronger initial launch accel
    LANDED_COUNT = 10*(1/FREQUENCY)  # Number of cycles needed to be exceeded to mark as landed

    acc_data = []   # 2d array
    qua_data = []   # 2d array
    time_data = []  # 1d array

    # File IO setup
    PATH_BLACKBOX = "blackbox.log"
    if(not os.path.isfile(f"{PATH_BLACKBOX}")):
        data_f = open(f"{PATH_BLACKBOX}", "w+")
    data_f = open(f"{PATH_BLACKBOX}", "w+")

    transmit_rf(rfm9x, "SETUP", count=10)


    ### PRE-LAUNCH STANDBY ###
    print("Waiting for launch...")
    while(not hasLaunched):
        time_thisSample = time.time()
        if(time_thisSample - time_lastSample >= FREQUENCY):
            time_lastSample = time_thisSample
            acc = imu.linear_acceleration

            # Guard against None values
            if(None not in acc):
                acc_accumulator.append(sum(acc))
            
        # Take average of latest 'ACC_WINDOW' elements of 'acc_accumulator' and check if above movement_threshold
        if(average_window(acc_accumulator, ACC_WINDOW) > MOTION_SENSITIVITY + MOTION_LAUNCH_SENSITIVITY):
            print("Launch detected!")
            LAUNCH_COORD = acquire_gps(gps, 10)
            hasLaunched = True
            break
            
        transmit_rf(rfm9x, f"Wait: t+{time_thisSample-time_launchStart} s")
    
    transmit_rf(rfm9x, "LAUNCH")
    if(LAUNCH_COORD is None):
        transmit_rf(rfm9x, "NO_LAUNCH_COORD")


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
            omg = imu.gyro
            qua = imu.quaternion

            # Blackbox recording (ACCx,y,z QUAx,y,z)
            data_f.write(f"{time_thisSample-time_launchStart}")
            data_f.write(f"{acc[0]}\t{acc[1]}\t{acc[2]}\t")
            data_f.write(f"{qua[0]}\t{qua[1]}\t{qua[2]}\t{qua[3]}\n")

            # Data recording
            time_data.append(time_thisSample-time_launchStart)
            acc_data.append(acc)
            qua_data.append(qua)

            if(None not in acc and None not in qua):
                acc_accumulator.append(sum(acc))
            # Check after some duration post launch for no motion (below movement_threshold)
            if((time_thisSample - time_launchStart >= MIN_IMU_TIME) and average_window(acc_accumulator, ACC_WINDOW) < MOTION_SENSITIVITY):
                motionless_count += 1
            else:
                motionless_count = 0    # Reset on motion detection

            if(motionless_count >= LANDED_COUNT):
                print("Landing detected!")
                print(f"Launch duration:{time_thisSample-time_launchStart}")
                LANDED_COORD = acquire_gps(gps, 10)
                hasLanded = True
                break

            transmit_rf(rfm9x, f"Launch: t+{time_thisSample-time_launchStart} s")

    transmit_rf(rfm9x, "LANDED\n", count=10)
    if(LANDED_COORD is None):
                transmit_rf(rfm9x, "NO_LANDING_COORD")
    data_f.close()

    ### POST-FLIGHT CALCULATION ###
    position_matrix = pos.acc_to_pos(acc_data, qua_data, time_data)
    coeff_matrix = (position_matrix[-1][0]/THE_COEFFICIENT, position_matrix[-1][1]/THE_COEFFICIENT, position_matrix[-1][2])

    # Calculate grid number
    grid_num = grid.calculate_grid(LAUNCH_COORD, coeff_matrix)
    
    if(LANDED_COORD is not None):
        grid_exp = grid.dist_between_coord(LAUNCH_COORD, LANDED_COORD)
    else:
        grid_exp = "No GPS Validation"
    str_grid = f'{grid_num}\r\n'
    str_exp  = f'{grid_exp}\r\n'
    
    # Save data
    print("Saved data to file!")
    with open("grid_number.txt", "w+") as file:
        file.write("Actual:\n")
        file.write(str_grid)
        file.write("\nExpected:\n")
        file.write(str_exp)
    
    with open("final_position.txt", "w+") as file:
        file.write(f"{position_matrix[-1][0]},{position_matrix[-1][1]}")

    # Transmit data
    print("Send signal loop...")
    while True:
        transmit_rf(rfm9x, f"KEY:{str_grid}")

if __name__ == '__main__':
    main()