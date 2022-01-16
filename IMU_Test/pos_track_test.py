import time
import numpy as np
import board
import adafruit_bno055
import scipy.integrate as it
from scipy.spatial.transform import Rotation as R

NOISE = 0.5
SAMPLES = 1000
SAMPLE_RATE = 100

i2c = board.I2C()
bno = adafruit_bno055.BNO055_I2C(i2c)
bno.mode = adafruit_bno055.IMUPLUS_MODE
bno.accel_range = adafruit_bno055.ACCEL_8G

def main():
    # Calibration step
    print("Calibrating BNO055...")
    while(bno.calibration_status[1] != 3 or bno.calibration_status[2] != 3):
        pass
    print("Calibrated!")

    while(input("Continue testing? (Y/n):").lower() == "y"):
        print("Collecting samples...")

        vals_acc = np.array([0,0,0])[np.newaxis]

        count = 0
        last_sample = time.monotonic()
        times = [0]          # Time steps

        while count < SAMPLES:
            this_sample = time.monotonic()

            if(this_sample-last_sample >= (1/SAMPLE_RATE)):
                count += 1
                last_sample = this_sample

                acc = bno.linear_acceleration   # m/s^2
                quat = bno.quaternion

                # Guard against Nonetype reads
                if(acc[0] is not None and quat[0] is not None):
                    # Filter noise
                    acc = filter_noise(acc, NOISE)
                    print(f"acc:{acc}")

                    # Calculate rotation matrix
                    r_mat = R.from_quat((*(quat[1:]), quat[0])).as_matrix()

                    # Transform acceleration vector to initialized frame
                    t_acc = r_mat.dot(np.array(acc))
                    print(f"tcc:{t_acc}")

                    # Record acceleration and time
                    vals_acc = np.append(vals_acc, np.array(t_acc)[np.newaxis], axis=0)
                    times.append(count/SAMPLE_RATE)

        print(f"vals_acc shape:{np.shape(vals_acc)}")
        print(f"times len:{len(times)}")
        # Calculate vel and disp (cumulative trapezoidal integration)            
        print("Calculating position...")
        calc_vel = map(lambda acc_arr: it.cumtrapz(acc_arr, times, initial=0), vals_acc.T)
        calc_pos = np.array(list(map(lambda vel_arr: it.cumtrapz(vel_arr, times, initial=0), calc_vel))).T

        print("Calculated positions")
        print(calc_pos)


def filter_noise(values, noise):
    filtered = []
    for value in values:
        filtered.append(0) if (value < noise) else filtered.append(value)
    return tuple(filtered)


if __name__ == '__main__':
    main()