import time
import numpy as np
import board
import adafruit_bno055
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

        calc_pos = np.array([])

        samples = SAMPLES
        last_sample = time.monotonic()
        v0 = (0,0,0)
        x0 = (0,0,0)

        while samples > 0:
            this_sample = time.monotonic()

            if(this_sample-last_sample >= (1/SAMPLE_RATE)):
                last_sample = this_sample

                acc = bno.linear_acceleration   # m/s^2
                quat = bno.quaternion

                # Guard against Nonetype reads
                if(acc[0] is not None and quat[0] is not None):
                    samples -= 1
                    
                    # Calculate rotation matrix
                    r_mat = R.from_quat((*(quat[1:]), quat[0])).as_matrix()

                    # Transform acceleration vector to initialized frame
                    t_acc = r_mat.dot(np.array(acc))

                    # Double integrate wrt sampling rate to calculate displacement
                    # disp = map(lambda a: 0.5*a*(1/SAMPLE_RATE**2), t_acc)  # prob wrong

                    # Calculate velocity and displacement
                    t_vel = (sum(k) for k in zip(v0, map(lambda a: a/SAMPLE_RATE, t_acc)))
                    t_disp = (sum(k) for k in zip(x0, map(lambda v: v/SAMPLE_RATE, t_vel)))
                    v0 = t_vel
                    x0 = t_disp

                    # Record displacement
                    np.append(calc_pos, t_disp)
                    print(t_disp)
                    print(type(t_disp))
                    print(calc_pos)

        print("Calculated positions")
        print(calc_pos)


if __name__ == '__main__':
    main()