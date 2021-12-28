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
        data = pd.read_csv(in_file,
                           sep='\t',
                           index_col=False)
        rate = 100   # in Hz
    
        # Extract data from columns (Each in a 3-vector of x,y,z)
        in_data = {
            'rate':rate,
            'acc':   data.filter(regex='Acc').values,
            'omega': data.filter(regex='Gyr').values}
        
        in_data['acc'] = pd.DataFrame(np.zeros((300, 3)))
        in_data['omega'] = pd.DataFrame(np.zeros((300, 3)))

        self._set_data(in_data)

samples = 300
count = 0

if __name__ == '__main__':
    rate = 100
    i2c = board.I2C()
    bno = adafruit_bno055.BNO055_I2C(i2c)
    bno.mode = adafruit_bno055.IMUPLUS_MODE

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
            if(acc[0] is None or omg[0] is None):
                continue

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

    bno = XSens(in_file='bno_data.txt')

    print("Processed data!\n")

    print(bno.pos)
