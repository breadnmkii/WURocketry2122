# External file for providing essential positioning functionality

# NOTE: Area: 5000x5000(ft^2), Grid: 250x250 (ft^2)
# TODO: GPS to grid algo
#       1. Get actual start,end gps coords
#       2. Get difference (ideal- actual) and correct actual coords
#       3. Get difference (end - start)
#       4. Convert to N/S, E/W distance measurements (meters)
#       5. Assuming our launchpad @ (0,0), convert our distances to grid based on grid length (76.2 m)
import math
from decimal import *


# Configuration & Constants
getcontext().prec = 7

IDEAL_COORD = (Decimal('38.649313'),Decimal('-90.311696'))  # The expected (lat,lon) coords, obtainted from our imager.py image
EARTH_CIRCUMFERENCE = 24901              # (miles)

    #return 5280*mile

def coord2feet(coord):
    return ((Decimal(f'{coord[0]}')/Decimal('360')) * Decimal(f'{EARTH_CIRCUMFERENCE}')*5280,
            (Decimal(f'{coord[1]}')/Decimal('360')) * Decimal(f'{EARTH_CIRCUMFERENCE}')*5280)

def coord2grid(launch_coord, current_coord):
    coord_correction = (Decimal(f'{IDEAL_COORD[0]}') - Decimal(f'{launch_coord[0]}'), 
                        Decimal(f'{IDEAL_COORD[1]}') - Decimal(f'{launch_coord[1]}'))

    distance_from_launch = (Decimal(f'{current_coord[0]}') - Decimal(f'{launch_coord[0]}') + coord_correction[0],
                            Decimal(f'{current_coord[1]}') - Decimal(f'{launch_coord[1]}') + coord_correction[1])

    return coord2feet(distance_from_launch)




def main():
    launch_coord = (38.649313, -90.311696)
    current_coord = (38.650501, -90.308958)
    print(coord2grid(current_coord, launch_coord))

if __name__=='__main__':
    main()


