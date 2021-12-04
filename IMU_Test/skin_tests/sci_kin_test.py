'''
Import data saved with XSens-sensors, through subclassing "IMU_Base"
'''

'''
Credit: Thomas Haslwanter
'''

import numpy as np
import pandas as pd
import abc

# To ensure that the relative path works
import os
import sys

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
                           skiprows=4, 
                           index_col=False)
    
        # Extract the columns that you want, and pass them on
        in_data = {'rate':rate,
               'acc':   data.filter(regex='Acc').values,
               'omega': data.filter(regex='Gyr').values,
               'mag':   data.filter(regex='Mag').values}
        self._set_data(in_data)

if __name__ == '__main__':
    bno = XSens(in_file='test_data.txt')

    print(bno.pos)


# import time
# import math
# import board
# import adafruit_bno055

# from skinematics.sensor.manual import MyOwnSensor


# i2c = board.I2C()
# sensor = adafruit_bno055.BNO055_I2C(i2c)

# # Initial skinematics sensor setup
# in_data = {'rate':   100.,
#             'acc':   sensor.acceleration,
#             'omega': sensor.gyro,
#             'mag':   sensor.magnetic}

# last_sample = time.monotonic()
# while True:
#     this_sample = time.monotonic()

#     if(this_sample-last_sample >= (1/100)):
#         last_sample = this_sample

#         # Do data collection/file writing here

# skin_sensor = MyOwnSensor(in_file='BNO055 Sensor', in_data=in_data)

