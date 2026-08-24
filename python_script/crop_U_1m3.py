"""
Crop 1 m³ full-domain U snapshots to enclosure interior.

Pixel coordinates derived analytically from camera parameters in
paraview_script_1m3_linux.py (IMG 3000×2000, ENC_Y ±1.5, ENC_Z 0–2.0,
MARGIN_TOP=0.08, MARGIN_BOT=0.22, MARGIN_SIDE=0.10).

Crop region: Y = [-0.48, 0.48] m (enclosure walls), Z = [0.0, 1.0] m.
Output: <case>/U/U_cropped/
"""

from PIL import Image
import os, glob, argparse

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── Camera parameters (paraview_script_1m3_linux.py) ─────────────────────────
IMG_W, IMG_H = 3000, 2000
Y_HALF       = 1.5
Z_HALF       = 1.0       # (ENC_Z_MAX - ENC_Z_MIN) / 2  = (2.0-0.0)/2
Y_CENTER     = 0.0
Z_CENTER     = 1.0 + 1.0 * (0.08 - 0.22)   # = 0.86
ASPECT       = IMG_W / IMG_H                 # = 1.5
ps_z         = Z_HALF * (1 + 0.08 + 0.22)   # = 1.30
ps_y         = Y_HALF * (1 + 2 * 0.10) / ASPECT  # = 1.20
PS           = max(ps_z, ps_y)               # = 1.30

VIEW_Y_HALF  = PS * ASPECT    # = 1.95 m
VIEW_Z_HALF  = PS             # = 1.30 m
VIEW_Y_MAX   = Y_CENTER + VIEW_Y_HALF   # +1.95
VIEW_Y_MIN   = Y_CENTER - VIEW_Y_HALF   # -1.95
VIEW_Z_MAX   = Z_CENTER + VIEW_Z_HALF   # +2.16
VIEW_Z_MIN   = Z_CENTER - VIEW_Z_HALF   # -0.44

# ── World → pixel (looking in +X, ViewUp=+Z → screen right = -Y) ─────────────
def world_to_pixel(Y, Z):
    px = (VIEW_Y_MAX - Y) / (VIEW_Y_MAX - VIEW_Y_MIN) * IMG_W
    py = (VIEW_Z_MAX - Z) / (VIEW_Z_MAX - VIEW_Z_MIN) * IMG_H
    return int(round(px)), int(round(py))

# ── Crop bounds ───────────────────────────────────────────────────────────────
CROP_Y_MAX =  0.48   # back wall (left in image)
CROP_Y_MIN = -0.48   # vent side (right in image)
CROP_Z_MAX =  1.0    # ceiling
CROP_Z_MIN =  0.0    # floor
PADDING    =  30

# Symmetric crop: enclosure walls at x≈1113 (left) and x≈1886 (right) in source.
# Right margin = 2002 - 1886 = 116 px; match on left: 1113 - 116 = 997.
px_left, py_top, px_right, py_bottom = 997, 867, 2002, 1687

print(f'Crop box  : left={px_left}, top={py_top}, right={px_right}, bottom={py_bottom}')
print(f'Crop size : {px_right - px_left} × {py_bottom - py_top} px')

# ── Cases ─────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument('cases', nargs='*', help='Case directory names (default: case 54)')
args = parser.parse_args()

cases = args.cases if args.cases else ['1m3_4mm_wall_H2_test_54']

for case in cases:
    u_dir   = os.path.join(BASE, case, 'U')
    out_dir = os.path.join(u_dir, 'U_cropped')
    os.makedirs(out_dir, exist_ok=True)
    pngs = sorted(glob.glob(os.path.join(u_dir, 'U_t*.png')))
    print(f'\n{case}: {len(pngs)} image(s)')
    for fpath in pngs:
        img     = Image.open(fpath)
        cropped = img.crop((px_left, py_top, px_right, py_bottom))
        out     = os.path.join(out_dir, os.path.basename(fpath))
        cropped.save(out)
        print(f'  {os.path.basename(fpath)} -> {cropped.size}')

print('\nDone.')
