# External file for providing essential grid position functionality

# NOTE:
# Area: 5000x5000(ft^2), Grid: 250x250 (ft^2)
# Center (0,0), -> is +x,  ^ is +y
# Latitude: N (+), S (-)    Longitude: E (+), W(-)
# Latitude = y-axis         Longitude = x-axis
# Coordinates in form of (y,x)

import math
from decimal import *

# Configuration & Constants
getcontext().prec = 7

## OFFICIAL NASA COORDINATES: (34.895444, -86.617000)  some farm in alabama

IDEAL_COORD = (Decimal('38.663484'),Decimal('-90.365707'))  # The expected (lat,lon) coords, obtainted from our imager.py image
EARTH_CIRCUMFERENCE = 24901     # (miles)
LAT_DEGREE          = 364000    # (feet)
LON_DEGREE          = 288200    # (feet)
MAP_LEN             = 5000      # (feet)
GRID_LEN            = 250       # (feet)
GRID_CEN            = 220       # (center grid_num)
GRID_ITV            = (MAP_LEN/GRID_LEN)+1    # Number of grid squares across either axis of map (21 squares)

# from LAND_COORD to IDEAL_COORD calculate x,y dist
#     above == below
# from LAUNCH_COORD to IDEAL_COORD calculate x,y dist
# add to IMU x,y dist

# calculate grid num from summed x,y dist from 0,0 center

## Function to convert two coordinantes A->B to distance
def coord_to_dist(coord_A, coord_B):
    return coord_to_feet((
        Decimal(f'{coord_B[0]}') - Decimal(f'{coord_A[0]}'),
        Decimal(f'{coord_B[1]}') - Decimal(f'{coord_A[1]}')))
## Helper function to convert two coordinates' degrees difference to feet
def coord_to_feet(coord):
    return ((Decimal(f'{coord[0]}')*Decimal(f'{LAT_DEGREE}')),
            (Decimal(f'{coord[1]}')*Decimal(f'{LON_DEGREE}')))

## Function to map launch distance to a grid number
# Distance passed should be total distance (either GPS or calculated) from origin (0,0 -> grid 220 center)
# 1. Calculates grid coordinate from (0,0)
# 2. Translates grid coordinate from (0,0) into grid number (i.e. (0,0) -> #220)
def dist_to_grid(launch_disp):
    grid_coord = tuple(map(lambda i: math.ceil(math.floor(2*i/GRID_LEN)/2), launch_disp))
    return GRID_CEN - (grid_coord[0]*GRID_ITV) + grid_coord[1]






## Test Script
def main():
    launch_coord = (38.663484, -90.365707)
    current_coord = (38.663050, -90.366002)
    imu_dist = (0,0)

    launch_diff = coord_to_dist(current_coord, IDEAL_COORD)
    abs_dist = (imu_dist[0]+launch_diff[0], imu_dist[1]+launch_diff[1])

    print(abs_dist)
    print(dist_to_grid(abs_dist))

if __name__=='__main__':
    main()


