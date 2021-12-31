# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import time
import math
import board
import adafruit_bno055


i2c = board.I2C()
sensor = adafruit_bno055.BNO055_I2C(i2c)
# sensor.mode = adafruit_bno055.IMUPLUS_MODE

# If you are going to use UART uncomment these lines
# uart = board.UART()
# sensor = adafruit_bno055.BNO055_UART(uart)

last_val = 0xFFFF


def temperature():
    global last_val  # pylint: disable=global-statement
    result = sensor.temperature
    if abs(result - last_val) == 128:
        result = sensor.temperature
        if abs(result - last_val) == 128:
            return 0b00111111 & result
    last_val = result
    return result


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
        print(f"Calibration Status:{sensor.calibration_status}")
        print()

""" Notes

Calibration status ranges from (0..3), 0 being uncalibrated.
Calibration status returns info as (system, gyro, accel, mag) sensors
  * Data should be ignored when sys cal == 0



"""
