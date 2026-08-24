"""
Crop 1 m³ zoomed-enclosure U velocity glyph snapshots to the enclosure interior.

Pixel coordinates derived analytically from camera parameters in
paraview_script_1m3_zoom_U_linux.py (IMG 3000×3000, ENC_Y ±0.5, ENC_Z 0-1.0,
MARGIN_TOP=0.05, MARGIN_BOT=0.20, MARGIN_SIDE=0.05).

Crops only the no-colorbar frames (U_zoom_t*.png); U_zoom_cb_t*.png frames
are skipped since the colorbar overlaps the crop region.

Output: <case>/U/U_cropped/
"""

from PIL import Image
import os, glob, argparse

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── Camera parameters (paraview_script_1m3_zoom_U_linux.py) ──────────────────
IMG_W, IMG_H = 3000, 3000
Y_HALF       = 0.5
Z_HALF       = 0.5       # (ENC_Z_MAX - ENC_Z_MIN) / 2 = (1.0-0.0)/2
Y_CENTER     = 0.0
Z_CENTER     = 0.5 + 0.5 * (0.05 - 0.20)     # = 0.425
ASPECT       = IMG_W / IMG_H                 # = 1.0
ps_z         = Z_HALF * (1 + 0.05 + 0.20)    # = 0.625
ps_y         = Y_HALF * (1 + 2 * 0.05) / ASPECT  # = 0.55
PS           = max(ps_z, ps_y)               # = 0.625

VIEW_Y_HALF  = PS * ASPECT    # = 0.625 m
VIEW_Z_HALF  = PS             # = 0.625 m
VIEW_Y_MAX   = Y_CENTER + VIEW_Y_HALF
VIEW_Y_MIN   = Y_CENTER - VIEW_Y_HALF
VIEW_Z_MAX   = Z_CENTER + VIEW_Z_HALF
VIEW_Z_MIN   = Z_CENTER - VIEW_Z_HALF

# ── World → pixel (looking in +X, ViewUp=+Z → screen right = -Y) ─────────────
def world_to_pixel(Y, Z):
    px = (VIEW_Y_MAX - Y) / (VIEW_Y_MAX - VIEW_Y_MIN) * IMG_W
    py = (VIEW_Z_MAX - Z) / (VIEW_Z_MAX - VIEW_Z_MIN) * IMG_H
    return px, py

# ── Crop bounds: enclosure interior, extended left/right/top to reveal the
# inflow (nozzle), outflow (vent), and flow just above the ceiling ───────────
# Note: rendered view only extends to Z=1.05 (ceiling + MARGIN_TOP*enclosure
# height), so CROP_Z_MAX is capped just under that to stay within the image.
CROP_Y_MAX =  0.6    # back wall (left in image) + 0.1 m margin
CROP_Y_MIN = -0.6    # vent side (right in image) + 0.1 m margin
CROP_Z_MAX =  1.04   # ceiling + ~0.04 m margin (view top is at 1.05)
CROP_Z_MIN =  0.0    # floor
PADDING    =  20

x0, y0 = world_to_pixel(CROP_Y_MAX, CROP_Z_MAX)   # top-left  (back wall, ceiling)
x1, y1 = world_to_pixel(CROP_Y_MIN, CROP_Z_MIN)   # bot-right (vent side, floor)
px_left, py_top, px_right, py_bottom = (
    int(round(x0)) - PADDING, int(round(y0)) - PADDING,
    int(round(x1)) + PADDING, int(round(y1)) + PADDING,
)

print(f'Crop box  : left={px_left}, top={py_top}, right={px_right}, bottom={py_bottom}')
print(f'Crop size : {px_right - px_left} × {py_bottom - py_top} px')

# ── Cases ─────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument('cases', nargs='*', help='Case directory names (default: case 76)')
args = parser.parse_args()

cases = args.cases if args.cases else ['1m3_4mm_wall_H2_test_76']

for case in cases:
    u_dir   = os.path.join(BASE, case, 'U', 'U_zoom')
    out_dir = os.path.join(BASE, case, 'U', 'U_cropped')
    os.makedirs(out_dir, exist_ok=True)
    pngs = sorted(glob.glob(os.path.join(u_dir, 'U_zoom_t*.png')))
    pngs = [p for p in pngs if '_cb_' not in os.path.basename(p)]
    print(f'\n{case}: {len(pngs)} image(s)')
    for fpath in pngs:
        img     = Image.open(fpath)
        cropped = img.crop((px_left, py_top, px_right, py_bottom))
        out     = os.path.join(out_dir, os.path.basename(fpath))
        cropped.save(out)
        print(f'  {os.path.basename(fpath)} -> {cropped.size}')

print('\nDone.')
