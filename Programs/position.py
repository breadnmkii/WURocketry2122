# External file for providing essential positioning functionality

# NOTE: Area: 5000x5000(ft^2), Grid: 250x250 (ft^2)
# TODO: GPS to grid algo
#       1. Get actual start,end gps coords
#       2. Get difference (actual - ideal) and correct actual coords
#       3. Get difference (end - start)
#       4. Convert to N/S, E/W distance measurements (meters)
#       5. Assuming our launchpad @ (0,0), convert our distances to grid based on grid length (76.2 m)
# Latitude: N (+), S (-)    Longitude: E (+), W(-)
# Latitude = y-axis         Longitude = x-axis
# So coordinates in form of (y,x)
import math
from decimal import *


# Configuration & Constants
getcontext().prec = 7

IDEAL_COORD = (Decimal('38.663484'),Decimal('-90.365707'))  # The expected (lat,lon) coords, obtainted from our imager.py image
EARTH_CIRCUMFERENCE = 24901     # (miles)
LAT_DEGREE          = 364000    # (feet)
LON_DEGREE          = 288200    # (feet)



## Function to convert coordinates from launch into launch distance
def coord_to_dist(launch_coord, current_coord):
    coord_correction = (Decimal(f'{launch_coord[0]}') - Decimal(f'{IDEAL_COORD[0]}'), 
                        Decimal(f'{launch_coord[1]}') - Decimal(f'{IDEAL_COORD[1]}'))

    return coord_to_feet((
        Decimal(f'{current_coord[0]}') - Decimal(f'{launch_coord[0]}') + coord_correction[0],
        Decimal(f'{current_coord[1]}') - Decimal(f'{launch_coord[1]}') + coord_correction[1]))

def coord_to_feet(coord):
    return ((Decimal(f'{coord[0]}')*Decimal(f'{LAT_DEGREE}')),
            (Decimal(f'{coord[1]}')*Decimal(f'{LON_DEGREE}')))

## Function to map launch distance to a grid number     NOTE: Center (0,0), -> is +x,  ^ is +y
# Assuming origin grid (0,0) is at center of map, then divide displacement vector components by grid length (250ft) and 
# apply ceiling to determine number of grids along x and y axis we are in
def dist_to_grid(launch_disp):
    x_grid = math.ceil((launch_disp[1])/250)
    y_grid = math.ceil((launch_disp[0])/250)

    return (x_grid, y_grid)
    
# Note: 3D vector in tuple of (x,y,z) 

## Function to integrate change in 3D linear acceleration vector into 3D velocity vector
# Note: linear acceleration measurement ignores acceleration due to gravity
# Step 1. 1-D velocity
# Step 2. 2-d velocity + change in orientation
# Step 3. enjoy dealing with 3d space
def integrate_laccel(t0, tf, delta_laccel):
    return tuple(map(lambda a: a*(tf-t0), delta_laccel))

# Maps a lambda function to add current displacement vector with current velocity vector
def update_disp(current_disp, current_vel):
    return tuple(map(lambda x: x[0] + x[1], zip(current_disp, current_vel)))

### DO we need this? should we just multiply current velocity vector by time to get
# ## Function to integrate change in 3D velocity vector into 3D displacement vector
# # Step 1. 1-D displacement
# # Step 2. 2-d displacement
# def integrate_veloc(t0, tf, delta_veloc):
#     return map(lambda a: (0.5)*a*(tf**2-t0**2), delta_veloc)

# test script
def main():
    launch_coord = (38.663484, -90.365707)
    current_coord = (38.663568, -90.366002)
    print(coord2grid(launch_coord, current_coord))

if __name__=='__main__':
    main()


