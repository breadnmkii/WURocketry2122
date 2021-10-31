import os, math
import urllib.request
from PIL import Image, ImageDraw

""" Note:
    The output image should be square and centered at specified coordinates, generally around (but under) 5000x5000ft^2, specified by 'max_gridlen' in meters
      - The 'metersPerPx' formula gives around +2.5% (~17ft) error for a zoom of 15
    
    Mudd field is around 672ft wide (along top), staticmap image gives 689ft

    Can place markers, given long/lat coords
"""

api_key = 'AIzaSyAkfPnwa9ZqUjB_etqfsG5Y4coMosDAlDI'


def main():
    ### Config
    filename = "pyra-grid"
    grid_itv = 76.2                    # Grid space intervals (meters)
    lat, lon = 38.649007,-90.310687     # Latitude, longitude
    maptype = 'satellite'               # Image type
    markers = ''                        # Optional image markers
    max_mapsize = 1524                  # Max length of map (meters)
    scale = 2                           # Resolution of image (max 2)
    zoom = 15                           # Zoom factor (optimal 15)

    # Calculate meters per pixel (from: https://stackoverflow.com/questions/9356724/google-map-api-zoom-range 
    # (no clue what that insane magic number is, but the source is a google employee so... all good))
    meters_per_px = (156543.03392 * math.cos(lat * math.pi / 180) / pow(2, zoom)) / scale
    size = math.floor(max_mapsize / (meters_per_px * scale))



    ### Output
    print("\n====================================================\n")
    print("Meters per pixel:", meters_per_px)
    print("Image size (px):", f"{size*scale}x{size*scale}")  # NOTE: This should match image dimensions, else accuracy is off!

    # Grabs image from Google Maps API and stores in /images directory
    getImage(filename, lat, lon, zoom, size, scale, maptype, markers)

    # Show square gridded image
    showGriddedImage(filename, grid_itv, max_mapsize, meters_per_px)

    print("\n====================================================\n")


def getImage(filename, lat, lon, zoom, size, scale, maptype, markers):
    # Make 'images' dir if DNE
    if not os.path.isdir('./images'):
        os.mkdir('./images')

    # Get image from url and save to file
    query = (
        f"https://maps.googleapis.com/maps/api/staticmap?"
        f"center={lat},{lon}&"
        f"zoom={math.floor(zoom)}&"
        f"size={size}x{size}&"
        f"scale={math.floor(scale)}&"
        f"maptype={maptype}&"
        f"key={api_key}"
    )
    urllib.request.urlretrieve(query, f"images/{filename}.png")

    print("Query:", query)


def showGriddedImage(filename, interval, length, meters_per_px):
    # Show image using pillow
    img = Image.open(f"images/{filename}.png")
    img_len = img.size[0]
    itv = 0

    draw = ImageDraw.Draw(img)
    color = (0,255,200)
    
    """ Perform Image processing here """
    for _ in range(math.ceil(length/interval)):
        vert_line = ((itv, 0), (itv,img_len))
        horz_line = ((0, itv), (img_len, itv))
        draw.line(vert_line, fill=color)
        draw.line(horz_line, fill=color)
        
        itv += interval/meters_per_px
    
    img.show()

    # Save gridded image
    img.save(f"images/{filename}-gridded.png")


if __name__ == "__main__":
    main()