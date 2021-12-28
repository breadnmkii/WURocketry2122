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
        print(f"Sample Time:{last_sample-this_sample}")
        last_sample = this_sample
        print(f"Gyroscope Data:{sensor.gyro}")
        print(f"Accelerometer Data:{sensor.acceleration}")
        print(f"Magnetometer Data:{sensor.magnetic}")
        #print("Accelerometer (m/s^2): {}".format(sensor.acceleration))
        #print("Magnetometer (microteslas): {}".format(sensor.magnetic))
        #print("Gyroscope (rad/sec): {}".format(sensor.gyro))
        print("Euler angle: {}".format(sensor.euler))
        #print("Quaternion: {}".format(sensor.quaternion))
        #print("Linear acceleration (m/s^2): {}".format(sensor.linear_acceleration))
        #print("Gravity (m/s^2): {}".format(sensor.gravity))
        print(sensor.calibration_status)
        print()
    
