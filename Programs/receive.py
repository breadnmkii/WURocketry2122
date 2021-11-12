import time
import busio
import board
from digitalio import DigitalInOut

# Import the RFM9x radio module.
import adafruit_rfm9x

# Configure RFM9x LoRa Radio
CS = DigitalInOut(board.CE1)
RESET = DigitalInOut(board.D25)
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)

file = open("receiving.txt", "w+")

while True:
    # Attempt setting up RFM9x Module
    try:
        rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, 915.0)
        rfm9x.tx_power = 23
        print('RFM9x successfully set up!')
        
        while True:
        
            count = 1
            # RX
            rx_packet = rfm9x.receive()
            if rx_packet is None:
                print('Did not receive')
            else:
                count += 1
                rx_data = str(rx_packet, "utf-8")
                if rx_data != None:
                    file.write(rx_data)
                f = open("receiving.txt", "r")
                print(f.read())
                time.sleep(1)
                
            if count==1000:
                file.close
    
    except RuntimeError as error:
        print('Error in setting up RFM9x... check wiring.')
    