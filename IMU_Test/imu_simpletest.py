# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import time
import math
import mathlib
import board
import adafruit_bno055

if __name__ == '__main__':
    i2c = board.I2C()
    sensor = adafruit_bno055.BNO055_I2C(i2c)

    # IMU Configuration

    sensor.mode = adafruit_bno055.IMUPLUS_MODE
    sensor.accel_range = adafruit_bno055.ACCEL_8G

    frequency_intv = 1/10
    last_sample = time.monotonic()

    max_quat_none = 1
    quat_wasNone = False
    max_acc_none = 1
    acc_wasNone = False
    
    while(sensor.calibration_status[1] != 3 or sensor.calibration_status[2] != 3):
        pass
      
    while True:
        this_sample = time.monotonic()
        if(this_sample - last_sample >= frequency_intv):
            last_sample = this_sample
            # print(f"Sample Time:{this_sample-last_sample}")
            # print(f"Gyroscope Data:{sensor.gyro}")
            # print(f"Accelerometer Data:{sensor.acceleration}")
            # print(f"Magnetometer Data:{sensor.magnetic}")
            # print("Euler angle: {}".format(sensor.euler))
            # print("Quaternion: {}".format(sensor.quaternion))
            # print(f"Linear Acceleration (m/s^2):{sensor.linear_acceleration}")
            # print(f"Gravity (m/s^2):{sensor.gravity}")
            quat = sensor.quaternion
            acc = sensor.linear_acceleration

            if(None in quat):
              if(quat_wasNone):
                max_quat_none += 1
              else:
                quat_wasNone = True
                print(f"Quat Gap: {max_quat_none}")
                max_quat_none = 1
            else:
              quat_wasNone = False

            if(None in acc):
              if(acc_wasNone):
                max_acc_none += 1
              else:
                acc_wasNone = True
                print(f"Acc Gap: {max_acc_none}")
                max_acc_none = 1
            else:
              acc_wasNone = False
              
              
            print(f"Absolute Orientation: {mathlib.quat_to_euler(quat[0],quat[1],quat[2],quat[3])}")
            print(f"Calibration Status:{sensor.calibration_status}")
            print()

""" Notes

Calibration status ranges from (0..3), 0 being uncalibrated.
Calibration status returns info as (system, gyro, accel, mag) sensors
  * Data should be ignored when sys cal == 0



"""
