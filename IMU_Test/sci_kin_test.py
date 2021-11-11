import time
import math
import board
import adafruit_bno055

from skinematics.sensor.manual import MyOwnSensor


i2c = board.I2C()
sensor = adafruit_bno055.BNO055_I2C(i2c)

# Initial skinematics sensor setup
in_data = {'rate':   100.,
            'acc':   sensor.acceleration,
            'omega': sensor.gyro,
            'mag':   sensor.mag}
skin_sensor = MyOwnSensor(in_file='BNO055 Sensor', in_data=in_data)

last_sample = time.monotonic()
while True:
    this_sample = time.monotonic()

    if(this_sample-last_sample >= (1/100)):
        last_sample = this_sample
        
        in_data = {'rate':   100.,
                    'acc':   sensor.acceleration,
                    'omega': sensor.gyro,
                    'mag':   sensor.mag}
        skin_sensor.calc_position()

        print(f'Velocity:{skin_sensor.vel}')
        print(f'Position:{skin_sensor.pos}\n')