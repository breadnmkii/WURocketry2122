# External file for providing essential positioning functionality

# NOTE: Area: 5000x5000(ft^2), Grid: 250x250 (ft^2)
# TODO: GPS to grid algo
#       1. Get actual start,end gps coords
#       2. Get difference (actual - ideal) and correct actual coords
#       3. Get difference (end - start)
#       4. Convert to N/S, E/W distance measurements (meters)
#       5. Assuming our launchpad @ (0,0), convert our distances to grid based on grid length (76.2 m)
# Latitude: N (+), S (-)   # Longitude: E (+), W(-)
import math
from decimal import *


# Configuration & Constants
getcontext().prec = 7

IDEAL_COORD = (Decimal('38.663484'),Decimal('-90.365707'))  # The expected (lat,lon) coords, obtainted from our imager.py image
EARTH_CIRCUMFERENCE = 24901     # (miles)
LAT_DEGREE          = 364000    # (feet)
LON_DEGREE          = 288200    # (feet)

    #return 5280*mile

def coord2feet(coord):
    return ((Decimal(f'{coord[0]}')*Decimal(f'{LAT_DEGREE}')),
            (Decimal(f'{coord[1]}')*Decimal(f'{LON_DEGREE}')))

# Since we know the image center will be at exactly half of 5000ft (2500,2500 ft), we can calculate distance from 
def coord2grid(launch_coord, current_coord):
    coord_correction = (Decimal(f'{launch_coord[0]}') - Decimal(f'{IDEAL_COORD[0]}'), 
                        Decimal(f'{launch_coord[1]}') - Decimal(f'{IDEAL_COORD[1]}'))

    distance_from_launch = (Decimal(f'{current_coord[0]}') - Decimal(f'{launch_coord[0]}') + coord_correction[0],
                            Decimal(f'{current_coord[1]}') - Decimal(f'{launch_coord[1]}') + coord_correction[1])

    return coord2feet(distance_from_launch)




def main():
    launch_coord = (38.663484, -90.365707)
    current_coord = (38.664766, -90.363024)
    print(coord2grid(launch_coord, current_coord))

if __name__=='__main__':
    main()


