"""
Crop 2 m³ full-domain U snapshots to enclosure interior.

Pixel coordinates are derived analytically from the camera parameters in
paraview_script_2m3_linux.py (IMG 3000×4000, ENC_Y ±1.5, ENC_Z 0–3.5,
MARGIN_TOP=0.08, MARGIN_BOT=0.22, MARGIN_SIDE=0.10).

Crop region: Y = [-0.62, 0.48] m (vent side extended), Z = [0.0, 2.1] m.
Output:  <case>/U/U_cropped/
"""

from PIL import Image
import os, glob

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── Camera parameters (paraview_script_2m3_linux.py) ─────────────────────────
IMG_W, IMG_H   = 3000, 4000
Y_HALF         = 1.5       # (ENC_Y_MAX - ENC_Y_MIN) / 2
Z_HALF         = 1.75      # (ENC_Z_MAX - ENC_Z_MIN) / 2
Y_CENTER       = 0.0
Z_CENTER       = 1.75 + 1.75 * (0.08 - 0.22)   # = 1.505
ASPECT         = IMG_W / IMG_H                   # = 0.75
ps_z           = Z_HALF * (1 + 0.08 + 0.22)     # = 2.275
ps_y           = Y_HALF * (1 + 2 * 0.10) / ASPECT  # = 2.4
PS             = max(ps_z, ps_y)                 # = 2.4  (height-limited)

VIEW_Y_HALF    = PS * ASPECT    # = 1.8 m
VIEW_Z_HALF    = PS             # = 2.4 m
VIEW_Y_MAX     = Y_CENTER + VIEW_Y_HALF   # +1.8
VIEW_Y_MIN     = Y_CENTER - VIEW_Y_HALF   # -1.8
VIEW_Z_MAX     = Z_CENTER + VIEW_Z_HALF   # +3.905
VIEW_Z_MIN     = Z_CENTER - VIEW_Z_HALF   # -0.895

# ── World → pixel (looking in +X, ViewUp=+Z → screen right = -Y) ─────────────
def world_to_pixel(Y, Z):
    px = (VIEW_Y_MAX - Y) / (VIEW_Y_MAX - VIEW_Y_MIN) * IMG_W
    py = (VIEW_Z_MAX - Z) / (VIEW_Z_MAX - VIEW_Z_MIN) * IMG_H
    return int(round(px)), int(round(py))

# ── Crop bounds ───────────────────────────────────────────────────────────────
CROP_Y_MAX =  0.48   # back wall (left in image)
CROP_Y_MIN = -0.62   # vent side, extended beyond -0.48 (right in image)
CROP_Z_MAX =  2.1    # ceiling
CROP_Z_MIN =  0.0    # floor
PADDING    =  30     # extra pixels around the crop box

px_left,  py_top    = world_to_pixel(CROP_Y_MAX, CROP_Z_MAX)
px_right, py_bottom = world_to_pixel(CROP_Y_MIN, CROP_Z_MIN)

px_left   = max(0,     px_left   - PADDING)
py_top    = max(0,     py_top    - PADDING)
px_right  = min(IMG_W, px_right  + PADDING)
py_bottom = min(IMG_H, py_bottom + PADDING)

print(f'Crop box  : left={px_left}, top={py_top}, right={px_right}, bottom={py_bottom}')
print(f'Crop size : {px_right - px_left} × {py_bottom - py_top} px')

# ── Cases ─────────────────────────────────────────────────────────────────────
CASES = [
    '2m3_27mm_wall_H2_test_56',
    '2m3_4mm_wall_H2_test_72',
]

for case in CASES:
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
