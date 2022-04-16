import time
import busio
import board
from digitalio import DigitalInOut
import RPi.GPIO as GPIO

# Import the RFM9x radio module.
import adafruit_rfm9x

# Configure GPIO pins
LED_PIN = 4
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(LED_PIN,GPIO.OUT)

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
        grid_f = open("RF_grid_number.txt", "w+")
        comm_f = open("RF_blackbox.txt", "w+")

        while True:
            # RX
            rx_packet = rfm9x.receive()
            if rx_packet:
                try:
                    rx_data = str(rx_packet, "utf-8")
                    if rx_data != None:
                        if(rx_data[:3] == "KEY"):
                            grid_f.write(rx_data+"\n")
                        else:
                            comm_f.write(rx_data)
                        print(f'Read: {rx_data}\n')
                except UnicodeDecodeError as err:
                    print("Unable to decode packet, skipping.")
    
    except RuntimeError as error:
        print('Error in setting up RFM9x... check wiring.')