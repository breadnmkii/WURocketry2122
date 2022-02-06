import time
import numpy as np
import pandas as pd

# To ensure that the relative path works
import os
import sys

# Sensor
import board
import RPi.GPIO as GPIO
import adafruit_bno055

from skinematics.imus import IMU_Base
from scipy.spatial.transform import Rotation as R

parent_dir = os.path.abspath(os.path.join( os.path.dirname(__file__), '..' ))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)


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


def filter_noise(values, noise):
    filtered = []
    for value in acc:
        filtered.append(0) if (value < noise) else filtered.append(value)
    return tuple(filtered)


if __name__ == '__main__':
    samples = 1000
    noise = 0.5
    count = 0
    rate = 100

    # GPIO Setup (6th Top-right pin is GPIO18)
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(18,GPIO.OUT)
    GPIO.output(18,GPIO.LOW)

    # BNO Setup
    i2c = board.I2C()
    bno = adafruit_bno055.BNO055_I2C(i2c)
    bno.mode = adafruit_bno055.IMUPLUS_MODE
    bno.accel_range = adafruit_bno055.ACCEL_8G

    # Calibration step
    print("Calibrating BNO055...")
    while(bno.calibration_status[1] != 3 or bno.calibration_status[2] != 3):
        pass
    print("Calibrated!")
    GPIO.output(18,GPIO.HIGH)   # Signal is calibrated

    while(input("Continue testing? (Y/n):").lower() == "y"):
        count = 0
        # init_orient = R.from_euler('zyx', [deg_N,90,0], degrees=True).as_matrix()   # Yaw, Pitch, Roll
        quat = bno.quaternion                        # [w,x,y,z]   scalar first format (Bosch + Skin convention)
        formatted_quat = (*(quat[1:]), quat[0])
        print(formatted_quat)
        init_orient = R.from_quat(formatted_quat).as_matrix()  # [x,y,z]+[w] scalar last format (Scipy convention)
        print(init_orient)

        time.sleep(3)
        data = {"Acc_X":[],
                "Acc_Y":[],
                "Acc_Z":[],
                "Gyr_X":[],
                "Gyr_Y":[],
                "Gyr_Z":[]}
        print("Collecting samples...")

        last_sample = time.monotonic()
        while count < samples:
            this_sample = time.monotonic()

            if(this_sample-last_sample >= (1/rate)):
                last_sample = this_sample

                acc = bno.linear_acceleration
                omg = bno.gyro

                # Guard against Nonetype reads
                if(None in acc or None in omg[0]):
                    continue
                
                # Noise filtering
                # acc = filter_noise(acc, noise)
                # omg = filter_noise(omg, noise)

                # Round values
                acc = list(map(lambda x: round(x, 6), acc))
                omg = list(map(lambda x: round(x, 6), omg))

                data["Acc_X"].append(acc[0])
                data["Acc_Y"].append(acc[1])
                data["Acc_Z"].append(acc[2])
                data["Gyr_X"].append(omg[0])
                data["Gyr_Y"].append(omg[1])
                data["Gyr_Z"].append(omg[2])

                count += 1
                
        print("Finished collection!\n")

        df = pd.DataFrame(data, index=None)
        df.to_csv("bno_data.txt", index=None, sep="\t", mode="w")
        
        print("Wrote data!\n")

        mySensor = XSens(in_file='bno_data.txt', R_init=init_orient)
        print(mySensor.calc_position())
        print("Processed data!\n")
        print(mySensor.pos)
        print(mySensor.quat)
