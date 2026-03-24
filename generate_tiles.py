# Generates XYZ PNG tiles per transmitter for Power BI Azure Maps
# Styling: #03787C @ 55%, thin borders, z4–z12

import os, math
from shapely import wkt
from shapely.ops import transform
from shapely.validation import make_valid
from pyproj import Transformer
from PIL import Image, ImageDraw
from shapely.geometry import box

FILL = (3, 120, 124, int(255 * 0.55))
BORDER = (2, 95, 98, 255)
TILE_SIZE = 256
ZOOMS = range(4, 13)

transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)

def project(x, y):
    return transformer.transform(x, y)

R = 6378137
ORIGIN_SHIFT = 2 * math.pi * R / 2
INIT_RES = 2 * math.pi * R / TILE_SIZE

def meters_to_pixels(mx, my, z):
    res = INIT_RES / (2 ** z)
    return ((mx + ORIGIN_SHIFT) / res, (ORIGIN_SHIFT - my) / res)

def tile_bounds(tx, ty, z):
    res = INIT_RES / (2 ** z)
    return (
        tx*TILE_SIZE*res - ORIGIN_SHIFT,
        ORIGIN_SHIFT - (ty+1)*TILE_SIZE*res,
        (tx+1)*TILE_SIZE*res - ORIGIN_SHIFT,
        ORIGIN_SHIFT - ty*TILE_SIZE*res
    )

with open("data/transmitters.wkt") as f:
    for line in f:
        name, geom_wkt = line.split("\t", 1)
        geom = make_valid(wkt.loads(geom_wkt.strip()))
        geom = transform(project, geom)

        for z in ZOOMS:
            minx, miny, maxx, maxy = geom.bounds
            px1, py1 = meters_to_pixels(minx, maxy, z)
            px2, py2 = meters_to_pixels(maxx, miny, z)

            for tx in range(int(px1//256), int(px2//256)+1):
                for ty in range(int(py1//256), int(py2//256)+1):
                    tile = box(*tile_bounds(tx, ty, z))
                    clipped = geom.intersection(tile)
                    if clipped.is_empty:
                        continue

                    img = Image.new("RGBA", (256,256),(0,0,0,0))
                    d = ImageDraw.Draw(img)

                    for poly in getattr(clipped, "geoms", [clipped]):
                        pts=[]
                        for x,y in poly.exterior.coords:
                            px,py = meters_to_pixels(x,y,z)
                            pts.append((px-tx*256, py-ty*256))
                        d.polygon(pts, fill=FILL, outline=BORDER)

                    path = f"output/{name.strip()}/tiles/{z}/{tx}"
                    os.makedirs(path, exist_ok=True)
                    img.save(f"{path}/{ty}.png")
``