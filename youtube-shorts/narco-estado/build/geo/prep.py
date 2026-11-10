import math, json, numpy as np
from PIL import Image, ImageDraw, ImageFilter
z, X0, X1, Y0, Y1 = 7, 21, 33, 51, 59
W, H = (X1 - X0 + 1) * 256, (Y1 - Y0 + 1) * 256
merc = np.zeros((H, W), np.float32)
for x in range(X0, X1 + 1):
    for y in range(Y0, Y1 + 1):
        a = np.asarray(Image.open(f't/{x}_{y}.png').convert('RGB')).astype(np.float32)
        merc[(y - Y0) * 256:(y - Y0 + 1) * 256, (x - X0) * 256:(x - X0 + 1) * 256] = a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768
# reproject to equirectangular lon/lat grid
LON0, LON1, LAT0, LAT1 = -118.5, -85.5, 13.5, 33.5
OW = 2400; OH = int(OW * (LAT1 - LAT0) / (LON1 - LON0)); n = 2 ** z
lon = np.linspace(LON0, LON1, OW); lat = np.linspace(LAT1, LAT0, OH)
px = ((lon + 180) / 360 * n - X0) * 256
py = ((1 - np.log(np.tan(np.radians(lat)) + 1 / np.cos(np.radians(lat))) / np.pi) / 2 * n - Y0) * 256
hgt = merc[np.clip(py.astype(int), 0, H - 1)[:, None], np.clip(px.astype(int), 0, W - 1)[None, :]]
# Mexico + land masks from Natural Earth 10m (topojson)
topo = json.load(open('../node_modules/world-atlas/countries-10m.json'))
sc, tr = topo['transform']['scale'], topo['transform']['translate']
arcs = []
for a in topo['arcs']:
    x = y = 0; pts = []
    for dx, dy in a: x += dx; y += dy; pts.append((x * sc[0] + tr[0], y * sc[1] + tr[1]))
    arcs.append(pts)
def ring(idx):
    out = []
    for i in idx:
        p = arcs[i] if i >= 0 else arcs[~i][::-1]
        out += p if not out else p[1:]
    return out
def polys(g):
    return [g['arcs']] if g['type'] == 'Polygon' else g['arcs']
toPix = lambda pts: [((lo - LON0) / (LON1 - LON0) * OW, (LAT1 - la) / (LAT1 - LAT0) * OH) for lo, la in pts]
mx = Image.new('L', (OW, OH), 0); land = Image.new('L', (OW, OH), 0)
dm, dl = ImageDraw.Draw(mx), ImageDraw.Draw(land)
outline = []
for g in topo['objects']['countries']['geometries']:
    for poly in polys(g):
        for k, r in enumerate(poly):
            pts = toPix(ring(r))
            if len(pts) < 3: continue
            dl.polygon(pts, fill=0 if k else 255)
            if g['properties']['name'] == 'Mexico':
                dm.polygon(pts, fill=0 if k else 255)
                if k == 0: outline.append(ring(r))
M = np.asarray(mx) > 127; L = np.asarray(land) > 127
json.dump([[[round(a, 3), round(b, 3)] for a, b in r] for r in outline if len(r) > 20], open('mexico_outline.json', 'w'))
# hillshade
e = hgt.copy(); e[~L] = np.minimum(e[~L], 0)
cell = (LON1 - LON0) / OW * 111000
gy, gx = np.gradient(e, cell)
az, alt = math.radians(315), math.radians(40)
slope = np.arctan(np.hypot(gx, gy) * 2.2); aspect = np.arctan2(-gx, gy)
shade = np.clip(np.sin(alt) * np.cos(slope) + np.cos(alt) * np.sin(slope) * np.cos(az - aspect), 0, 1)
# hypsometric tint (lowland green -> tan -> brown -> snow)
stops = [(0, (52, 92, 52)), (300, (96, 128, 68)), (900, (170, 160, 104)), (1600, (168, 122, 78)), (2600, (130, 92, 66)), (3800, (220, 214, 206)), (5600, (255, 255, 255))]
def tint(h):
    out = np.zeros(h.shape + (3,), np.float32); hs = np.clip(h, 0, 5600)
    for (h0, c0), (h1, c1) in zip(stops, stops[1:]):
        m = (hs >= h0) & (hs <= h1); t = ((hs - h0) / (h1 - h0))[m][:, None]
        out[m] = np.array(c0) * (1 - t) + np.array(c1) * t
    return out
col = tint(hgt) * (0.35 + 0.85 * shade[..., None])
# neighbours: desaturated & dark; ocean: deep navy with bathymetry
grey = col.mean(-1, keepdims=True)
col[L & ~M] = (grey[L & ~M] * .45 + np.array([10, 12, 16]))
depth = np.clip(-hgt / 5000, 0, 1)[..., None]
ocean = np.array([14, 48, 72]) * (1 - depth) + np.array([3, 10, 22]) * depth
col[~L] = ocean[~L] * (0.75 + .4 * shade[~L][:, None])
img = Image.fromarray(np.clip(col, 0, 255).astype(np.uint8))
img.save('relief.jpg', quality=92)
# height grid for the mesh (metres), Mexico+land only, ocean floor kept shallow
g = hgt.copy(); g[~L] = np.maximum(g[~L], -400) * .2
small = np.asarray(Image.fromarray(g).resize((600, int(600 * OH / OW)), Image.BILINEAR), np.float32)
small.astype('<f4').tofile('height.bin')
Image.fromarray((M * 255).astype(np.uint8)).resize((1200, int(1200 * OH / OW))).save('mask.png')
json.dump({'w': small.shape[1], 'h': small.shape[0], 'lon': [LON0, LON1], 'lat': [LAT0, LAT1]}, open('height.json', 'w'))
print(OW, OH, small.shape, hgt.max(), hgt.min())
