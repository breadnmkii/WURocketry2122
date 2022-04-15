# SPDX-FileCopyrightText: 2018 Brent Rubell for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
Wiring Check, Pi Radio w/RFM9x

Learn Guide: https://learn.adafruit.com/lora-and-lorawan-for-raspberry-pi
Author: Brent Rubell for Adafruit Industries
"""
"""
 Pins
   19 - MOSI
   21 - MISO
   22 - RST
   23 - SCK
   26 - CS
   
"""

import time
import datetime     # for testing
import busio
import board
from digitalio import DigitalInOut

# Import the RFM9x radio module.
import adafruit_rfm9x

# Configure RFM9x LoRa Radio
CS = DigitalInOut(board.CE1)
RESET = DigitalInOut(board.D25)
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)

# Configure radio frequencies
rf_channel = 7
rf_freq = 434.550 + rf_channel * 0.1

while True:
    # Attempt setting up RFM9x Module
    try:
        rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, rf_freq)
        rfm9x.tx_power = 23
        print('RFM9x successfully set up!')
        f = open("rf_test.txt", "w+")
        f.write(f"Collection started: {datetime.datetime.now()}\n")
        
        while True:
            # RX
            rx_packet = rfm9x.receive()
            if rx_packet:
                receive_time = time.time_ns()
                rx_data = str(rx_packet, "utf-8")
                f.write(f'{receive_time} <- {rx_data}\n')
                print(f'{receive_time} <- {rx_data}')

    except RuntimeError as err:
        print("Error setting up, check wiring")
