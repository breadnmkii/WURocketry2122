# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import time
import math
import board
import adafruit_bno055

def quat_to_euler(x, y, z, w):
        """
        Convert a quaternion into euler angles (roll, pitch, yaw)
        roll is rotation around x in radians (counterclockwise)
        pitch is rotation around y in radians (counterclockwise)
        yaw is rotation around z in radians (counterclockwise)
        """
        t0 = +2.0 * (w * x + y * z)
        t1 = +1.0 - 2.0 * (x * x + y * y)
        roll_x = math.atan2(t0, t1)
     
        t2 = +2.0 * (w * y - z * x)
        t2 = +1.0 if t2 > +1.0 else t2
        t2 = -1.0 if t2 < -1.0 else t2
        pitch_y = math.asin(t2)
     
        t3 = +2.0 * (w * z + x * y)
        t4 = +1.0 - 2.0 * (y * y + z * z)
        yaw_z = math.atan2(t3, t4)
     
        return roll_x, pitch_y, yaw_z # in radians

if __name__ == '__main__':
    i2c = board.I2C()
    sensor = adafruit_bno055.BNO055_I2C(i2c)

    # IMU Configuration

    # sensor.mode = adafruit_bno055.IMUPLUS_MODE
    sensor.accel_range(rng=ACCEL_86)

    frequency_intv = 1/10
    last_sample = time.monotonic()
    while True:
        this_sample = time.monotonic()
        if(this_sample - last_sample >= frequency_intv):
            print(f"Sample Time:{this_sample-last_sample}")
            last_sample = this_sample
            print(f"Gyroscope Data:{sensor.gyro}")
            print(f"Accelerometer Data:{sensor.acceleration}")
            # print(f"Magnetometer Data:{sensor.magnetic}")
            # print("Euler angle: {}".format(sensor.euler))
            #print("Quaternion: {}".format(sensor.quaternion))
            print(f"Linear Acceleration (m/s^2):{sensor.linear_acceleration}")
            print(f"Gravity (m/s^2):{sensor.gravity}")
            print(f"Absolute Orientation: {sensor.quaternion.toEuler()}")
            print(f"Calibration Status:{sensor.calibration_status}")
            print()

""" Notes

Calibration status ranges from (0..3), 0 being uncalibrated.
Calibration status returns info as (system, gyro, accel, mag) sensors
  * Data should be ignored when sys cal == 0



"""
