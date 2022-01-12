import time
import numpy as np
import board
import adafruit_bno055
import scipy.integrate as it
from scipy.spatial.transform import Rotation as R


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

        vals_acc = np.array([])

        samples = SAMPLES
        last_sample = time.monotonic()
        v0 = (0,0,0)
        x0 = (0,0,0)
        times = []          # Time steps

        while samples > 0:
            this_sample = time.monotonic()

            if(this_sample-last_sample >= (1/SAMPLE_RATE)):
                last_sample = this_sample

                acc = bno.linear_acceleration   # m/s^2
                quat = bno.quaternion
                times.append(1/SAMPLE_RATE)

                # Guard against Nonetype reads
                if(acc[0] is not None and quat[0] is not None):
                    samples -= 1
                    
                    # Calculate rotation matrix
                    r_mat = R.from_quat((*(quat[1:]), quat[0])).as_matrix()

                    # Transform acceleration vector to initialized frame
                    t_acc = r_mat.dot(np.array(acc))

                    # Record acceleration
                    np.append(vals_acc, t_acc[np.newaxis], axis=0)
        print(t_acc)
        # Calculate vel and disp (cumulative trapezoidal integration)            
        print("Calculating position...")
        calc_vel = map(lambda acc_arr: it.cumtrapz(acc_arr, times, initial=0), t_acc.T)
        calc_pos = map(lambda vel_arr: it.cumtrapz(vel_arr, times, initial=0), calc_vel)

        print("Calculated positions")
        print(calc_pos)


if __name__ == '__main__':
    main()