"""
crop_snapshots_2m3.py — Crop edges from 2 m³ enclosure ParaView snapshot PNGs.

Image size: 3000×4000 px (portrait orientation).

Crop defaults (pixels):
    top    = 418   (removes white space + time label + ceiling strip artifacts)
    bottom = 737   (~10 px below domain bottom, removes white gap + colorbar)
    left   = 240   (~10 px margin)
    right  = 241   (~10 px margin)

Usage:
    python3 crop_snapshots_2m3.py <input_dir> [options]

    Crops all *.png files in <input_dir> and writes results to
    <input_dir>/cropped/ by default.

Examples:
    python3 crop_snapshots_2m3.py ../2m3_27mm_wall_H2_test_56/H2_vol_con
    python3 crop_snapshots_2m3.py ../2m3_4mm_wall_H2_test_72/H2_vol_con --top 350
"""

import argparse
import os
import sys
from pathlib import Path
from PIL import Image


def parse_args():
    parser = argparse.ArgumentParser(
        description="Crop edges from 2 m³ enclosure ParaView snapshot PNGs."
    )
    parser.add_argument("input_dir", help="Directory containing PNG snapshots")
    parser.add_argument("--top",     type=int, default=418,
                        help="Pixels to crop from top (default: 418 — removes white space + time label + ceiling strips)")
    parser.add_argument("--bottom",  type=int, default=737,
                        help="Pixels to crop from bottom (default: 737 — removes colorbar + white gap, ~10 px margin)")
    parser.add_argument("--left",    type=int, default=240,
                        help="Pixels to crop from left (default: 240 — ~10 px margin)")
    parser.add_argument("--right",   type=int, default=241,
                        help="Pixels to crop from right (default: 241 — ~10 px margin)")
    parser.add_argument("--inplace", action="store_true",
                        help="Overwrite originals instead of writing to cropped/ subfolder")
    parser.add_argument("--suffix",  default="",
                        help="Suffix to append to output filenames (ignored with --inplace)")
    return parser.parse_args()


def crop_image(src_path, dst_path, top, bottom, left, right):
    img = Image.open(src_path)
    w, h = img.size
    box = (left, top, w - right if right else w, h - bottom if bottom else h)
    cropped = img.crop(box)
    cropped.save(dst_path)
    return img.size, cropped.size


def main():
    args = parse_args()
    input_dir = Path(args.input_dir).resolve()

    if not input_dir.is_dir():
        sys.exit(f"ERROR: not a directory: {input_dir}")

    pngs = sorted(input_dir.glob("*.png"))
    if not pngs:
        sys.exit(f"ERROR: no PNG files found in {input_dir}")

    if args.inplace:
        out_dir = input_dir
    else:
        out_dir = input_dir / "cropped"
        out_dir.mkdir(exist_ok=True)

    print(f"Input : {input_dir}  ({len(pngs)} PNG files)")
    print(f"Output: {out_dir}")
    print(f"Crop  : top={args.top}  bottom={args.bottom}  left={args.left}  right={args.right}")
    print()

    for src in pngs:
        stem = src.stem + args.suffix if not args.inplace else src.stem
        dst  = out_dir / (stem + ".png")
        orig_size, new_size = crop_image(src, dst, args.top, args.bottom, args.left, args.right)
        print(f"  {src.name}  {orig_size[0]}×{orig_size[1]} → {new_size[0]}×{new_size[1]}  →  {dst.name}")

    print(f"\nDone. {len(pngs)} image(s) cropped.")


if __name__ == "__main__":
    main()
