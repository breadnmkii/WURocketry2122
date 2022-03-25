import time
import average as avg
import numpy as np
import board
import adafruit_bno055
import scipy.integrate as it
from scipy.spatial.transform import Rotation as R

NOISE = 0.5
SAMPLE_RATE = 100

i2c = board.I2C()
bno = adafruit_bno055.BNO055_I2C(i2c)
bno.mode = adafruit_bno055.IMUPLUS_MODE
bno.accel_range = adafruit_bno055.ACCEL_16G

def acc_to_pos(data_acc, data_qua, data_time):
    samples = len(data_time)

    data_acc = np.array(avg.average_acc(avg.data_none(np.array(data_acc))))
    data_qua = np.array(avg.data_none(np.array(data_qua)))
    data_rot = np.array(list(map(lambda q: R.from_quat((*(q[1:]), q[0])).as_matrix(), data_qua)))
    abs_acc = []
    for i in range(samples):
        abs_acc.append(np.dot(data_rot[i],data_acc[i]))

    # Calculate vel and disp (cumulative trapezoidal integration)            
    print("Calculating position...")
    calc_vel = map(lambda acc_arr: it.cumtrapz(acc_arr, data_time, initial=0), data_acc.T)
    calc_pos = np.array(list(map(lambda vel_arr: it.cumtrapz(vel_arr, data_time, initial=0), calc_vel))).T

    print("Calculated positions")
    print(calc_pos)

    return calc_pos


def filter_noise(values, noise):
    filtered = []
    for value in values:
        filtered.append(0) if (value < noise) else filtered.append(value)
    return tuple(filtered)