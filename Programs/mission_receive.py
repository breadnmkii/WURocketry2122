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

# Validity count to ensure at least 'n' samples of grid_number is received
valid_count = 5

while valid_count > 0:
    # Attempt setting up RFM9x Module
    try:
        rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, 433.0)
        rfm9x.tx_power = 23
        print('RFM9x successfully set up!')
        grid_f = open("files/grid_number.txt", "w+")
        comm_f = open("files/blackbox.txt", "w+")

        while True:
            # RX
            rx_packet = rfm9x.receive()
            if rx_packet is None:
                print('Fail\n')
            else:
                rx_data = str(rx_packet, "utf-8")
                if rx_data != None:
                    print(f'Read: {rx_data}\n')
                    if(rx_data[:3] == "KEY"):
                        grid_f.write(rx_data+"\n")
                        valid_count -= 1
                    else:
                        comm_f.write(rx_data)
            if valid_count < 0:
                grid_f.close()
                comm_f.close()
                break

            time.sleep(0.1)
    
    except RuntimeError as error:
        print('Error in setting up RFM9x... check wiring.')

GPIO.output(LED_PIN, GPIO.HIGH)
time.sleep(999999)