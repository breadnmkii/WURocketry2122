'''
Import data saved with XSens-sensors, through subclassing "IMU_Base"
'''

'''
Credit: Thomas Haslwanter
'''
import time
import math
import numpy as np
import pandas as pd
import abc

# To ensure that the relative path works
import os
import sys

# Sensor
import board
import adafruit_bno055

parent_dir = os.path.abspath(os.path.join( os.path.dirname(__file__), '..' ))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

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
                           index_col=False)
    
        # Extract data from columns (Each in a 3-vector of x,y,z)
        in_data = {'rate':rate,
               'acc':   data.filter(regex='Acc').values,
               'omega': data.filter(regex='Gyr').values,
               'mag':   data.filter(regex='Mag').values}
        self._set_data(in_data)

samples = 100
count = 0

if __name__ == '__main__':
    rate = 100
    i2c = board.I2C()
    bno = adafruit_bno055.BNO055_I2C(i2c)

    data = {"Acc_X":[],
            "Acc_Y":[],
            "Acc_Z":[],
            "Gyr_X":[],
            "Gyr_Y":[],
            "Gyr_Z":[],
            "Mag_X":[],
            "Mag_Y":[],
            "Mag_Z":[],
            "Qua_W":[],
            "Qua_X":[],
            "Qua_Y":[],
            "Qua_Z":[]}
    
    print("Collecting samples...")

    last_sample = time.monotonic()
    while count < samples:
        this_sample = time.monotonic()

        if(this_sample-last_sample >= (1/rate)):
            last_sample = this_sample

            acc = bno.linear_acceleration
            omg = bno.gyro
            mag = bno.magnetic
            qua = bno.quaternion
            
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

            count += 1
            
    print("Finished collection!\n")

    df = pd.DataFrame(data, index=None)
    df.to_csv("bno_data.txt", index=None, sep="\t", mode="a")
    
    print("Wrote data!\n")

    # bno = XSens(in_file='bno_data.txt')

    # print("Processed data!\n")

    # print(bno.pos)
