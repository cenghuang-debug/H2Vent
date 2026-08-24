"""
Crop the velocity colorbar strip from 1 m³ zoomed-enclosure U glyph snapshots
(paraview_script_1m3_zoom_U_linux.py output, U_zoom_cb_t*.png, 3000x3000 px).

Crop box located by scanning for non-white pixels below the enclosure floor
in the case-76 reference image (title + tick labels + gradient bar span rows
2634-2939, cols 156-2842); padded by 30 px:
    left=126, top=2604, right=2872, bottom=2969

Usage:
    python3 crop_U_colorbar_zoom_1m3.py [case_name ...]

    Reads  <case>/U/U_zoom/U_zoom_cb_t*.png  (uses last timestep if multiple)
    Writes <case>/U/U_zoom_colorbar.png
"""

from PIL import Image
import os, glob, argparse

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CROP_LEFT   = 126
CROP_TOP    = 2604
CROP_RIGHT  = 2872
CROP_BOTTOM = 2969

parser = argparse.ArgumentParser()
parser.add_argument('cases', nargs='*', default=['1m3_4mm_wall_H2_test_76'])
args = parser.parse_args()

for case in args.cases:
    u_dir = os.path.join(BASE, case, 'U', 'U_zoom')
    pngs  = sorted(glob.glob(os.path.join(u_dir, 'U_zoom_cb_t*.png')))
    if not pngs:
        print(f'{case}: no U_zoom_cb_t*.png found, skipping.')
        continue
    src_path = pngs[-1]
    img = Image.open(src_path)
    cb  = img.crop((CROP_LEFT, CROP_TOP, CROP_RIGHT, CROP_BOTTOM))

    out = os.path.join(BASE, case, 'U', 'U_zoom_colorbar.png')
    cb.save(out)
    print(f'{case}: {os.path.basename(src_path)} -> U_zoom_colorbar.png {cb.size}')

print('Done.')
