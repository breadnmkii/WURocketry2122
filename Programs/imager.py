import os, math
import urllib.request
from PIL import Image, ImageDraw, ImageFont

""" Note:
    The output image should be square and centered at specified coordinates, generally around (but under) 5000x5000ft^2, specified by 'max_gridlen' in meters
      - The 'metersPerPx' formula gives around +2.5% (~17ft) error for a zoom of 15
    
    Mudd field is around 672ft wide (along top), staticmap image gives 689ft

    Can place markers, given long/lat coords
"""

api_key = 'AIzaSyBeo0CTYJ9hYSpUaQW8i_wCqR4S04J7-J0'


def main():
    ### Config
    filename = "pyra-grid"
    grid_itv = 76.2                     # Grid space intervals (meters)
    lat, lon = 38.64871999597565, -90.30274973493445 #34.895444, -86.617000    # 38.649007,-90.310687     # Latitude, longitude
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
    print("Grid scale (m):", grid_itv)
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
    img = Image.open(f"images/{filename}.png").convert("RGBA")
    txt = Image.new("RGBA", img.size, (255,255,255,0))
    img_len = img.size[0]
    grid_itv = 0
    grid_num = 0
    GRIDS = math.ceil(length/interval)
    INCREMENT = interval/meters_per_px

    fnt = ImageFont.load_default()
    
    color = (0,255,200)
    draw = ImageDraw.Draw(img)
    write = ImageDraw.Draw(txt)
    
    """ Perform Image processing here """
    for y in range(GRIDS):
        vert_line = ((grid_itv, 0), (grid_itv,img_len))
        horz_line = ((0, grid_itv), (img_len, grid_itv))
        draw.line(vert_line, fill=color)
        draw.line(horz_line, fill=color)

        for i in range(GRIDS):
            write.text((i*INCREMENT+3,y*INCREMENT), f"{i+grid_num}", color, font=fnt)
        grid_num += GRIDS
             
        
        grid_itv += INCREMENT
    out = Image.alpha_composite(img, txt)
    out.show()

    # Save gridded image
    out.save(f"images/{filename}-gridded.png")


if __name__ == "__main__":
    main()