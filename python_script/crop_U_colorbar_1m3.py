"""
Crop the velocity colorbar strip from 1 m³ U field snapshots.

Crop box matched to case 55 reference (2660×280 px):
    left=170, top=1720, right=2830, bottom=2000

Usage:
    python3 crop_U_colorbar_1m3.py [case_name ...]

    Reads  <case>/U/U_t*.png  (uses last timestep if multiple)
    Writes <case>/U/U_colorbar.png
"""

from PIL import Image, ImageDraw
import numpy as np
import os, glob, argparse

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CROP_LEFT   = 170
CROP_TOP    = 1700
CROP_RIGHT  = 2830
CROP_BOTTOM = 2000

parser = argparse.ArgumentParser()
parser.add_argument('cases', nargs='*', default=['1m3_4mm_wall_H2_test_54'])
args = parser.parse_args()

for case in args.cases:
    u_dir = os.path.join(BASE, case, 'U')
    pngs  = sorted(glob.glob(os.path.join(u_dir, 'U_t*.png')))
    if not pngs:
        print(f'{case}: no U_t*.png found, skipping.')
        continue
    src_path = pngs[-1]
    img = Image.open(src_path)
    cb  = img.crop((CROP_LEFT, CROP_TOP, CROP_RIGHT, CROP_BOTTOM))

    # Remove any arrow-tip artifact in top rows (dark pixels left of title centre)
    arr  = np.array(cb)
    draw = ImageDraw.Draw(cb)
    for row in range(30):
        dark = np.where(arr[row, :, :].max(axis=1) < 150)[0]
        artifact = dark[dark < 1050]
        if len(artifact):
            x0, x1 = int(artifact[0]) - 5, int(artifact[-1]) + 5
            draw.rectangle([x0, row, x1, row], fill=(255, 255, 255))

    out = os.path.join(u_dir, 'U_colorbar.png')
    cb.save(out)
    print(f'{case}: {os.path.basename(src_path)} -> U_colorbar.png {cb.size}')

print('Done.')
