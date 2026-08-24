"""
Crop the X_H2 colorbar strip from H2_vol_con snapshots.

Crop box matched to case 76 reference (white -> yellow -> red colormap,
2646x320 px on a 3000x2000 source):
    left=172, top=1665, right=2818, bottom=1985

Usage:
    python3 crop_H2_colorbar.py [case_name ...]

    Reads  <case>/H2_vol_con/H2_vol_con_t*.png  (uses last timestep if multiple)
    Writes <case>/H2_vol_con/colorbar_X_H2.png
"""

from PIL import Image
import os, glob, argparse

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CROP_LEFT   = 172
CROP_TOP    = 1665
CROP_RIGHT  = 2818
CROP_BOTTOM = 1985

parser = argparse.ArgumentParser()
parser.add_argument('cases', nargs='*', default=['1m3_4mm_wall_H2_test_76'])
args = parser.parse_args()

for case in args.cases:
    h2_dir = os.path.join(BASE, case, 'H2_vol_con')
    pngs   = sorted(glob.glob(os.path.join(h2_dir, 'H2_vol_con_t*.png')))
    if not pngs:
        print(f'{case}: no H2_vol_con_t*.png found, skipping.')
        continue
    src_path = pngs[-1]
    img = Image.open(src_path)
    cb  = img.crop((CROP_LEFT, CROP_TOP, CROP_RIGHT, CROP_BOTTOM))

    out = os.path.join(h2_dir, 'colorbar_X_H2.png')
    cb.save(out)
    print(f'{case}: {os.path.basename(src_path)} -> colorbar_X_H2.png {cb.size}')

print('Done.')
