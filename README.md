# WURocketry2122
WU Rocketry 21-22 Payload Repository

~ hello from pi!

Setup:

    sudo apt-get update

    sudo apt-get upgrade

    sudo apt-get install python3-pip

    sudo pip3 install --upgrade setuptools
    
    sudo apt-get install libatlas-base-dev
    

Recommended to use venvs for each individual 3rd-party library (separate non-core dependencies)

Core Library Dependencies:

    pip install Pillow; pip3 install Adafruit-Blinka; pip3 install adafruit-circuitpython-gps; pip3 install adafruit-circuitpython-bno055; pip3 install adafruit-circuitpython-rfm9x
    
Dependencies (LibofRelax IMU Tracking):

    pip3 install numpy; pip3 install scipy

Dependencies (scikit-kinematics IMU Library):
   
    pip install scikit-kinematics

* Update With: **pip install --upgrade --no-deps scikit-kinematics**
