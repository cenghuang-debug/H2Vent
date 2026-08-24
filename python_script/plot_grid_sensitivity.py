"""
plot_grid_sensitivity.py — Grid sensitivity plot: ceiling H2 time history for two mesh cases.

Uses back-wall probes (opposite to vents), matching the experimental sensor placement
in Bernard-Michel & Houssin-Agbomson (2017), Fig. 2.

Usage:
    python3 plot_grid_sensitivity.py <case_fine> <case_coarse> [--xlim 30] [--exp 2.52]

Arguments:
    case_fine    Case number for the fine mesh
    case_coarse  Case number for the coarse mesh
    --xlim       Upper x-axis limit in seconds (default: 30)
    --exp        Experimental reference value in vol% (omit to suppress line)

Examples:
    python3 plot_grid_sensitivity.py 61 73
    python3 plot_grid_sensitivity.py 61 73 --xlim 80 --exp 2.52
"""

import argparse
import glob
import re
import numpy as np
import matplotlib.pyplot as plt
import os, sys

sys.path.insert(0, os.path.dirname(__file__))
from plot_style import apply_style, GOLDEN_WIDTH, GOLDEN_HEIGHT, LW, save_figure

M_H2  = 0.002016
M_air = 0.028970

def mass_to_vol_frac(Y):
    X = (Y / M_H2) / (Y / M_H2 + (1.0 - Y) / M_air)
    return X * 100.0

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")

def find_case_dir(case_num):
    pattern = os.path.join(BASE_DIR, f"*_H2_test_{case_num:02d}")
    matches = glob.glob(pattern)
    return matches[0] if matches else None

def read_probe_positions(probe_file):
    z_coords = []
    with open(probe_file) as f:
        for line in f:
            if not line.startswith("#"):
                break
            m = re.match(r"#\s*Probe\s+\d+\s+\([\d.e+-]+\s+[\d.e+-]+\s+([\d.e+-]+)\)", line)
            if m:
                z_coords.append(float(m.group(1)))
    return z_coords

def read_ceiling_probe(case_num):
    case_dir = find_case_dir(case_num)
    if case_dir is None:
        return None, None, None
    probe_dir = os.path.join(case_dir, "postProcessing", "probes_H2_vertical_back")
    if not os.path.exists(probe_dir):
        return None, None, None

    time_folders = sorted(
        [d for d in os.listdir(probe_dir) if d.replace('.', '', 1).isdigit()],
        key=lambda x: float(x)
    )
    if not time_folders:
        return None, None, None

    first_file = os.path.join(probe_dir, time_folders[0], "H2")
    z_coords = read_probe_positions(first_file)
    ceiling_idx = int(np.argmax(z_coords)) if z_coords else 0
    ceiling_z   = z_coords[ceiling_idx] if z_coords else None

    times, vals = [], []
    last_time = -1.0
    for folder in time_folders:
        probe_file = os.path.join(probe_dir, folder, "H2")
        if not os.path.exists(probe_file):
            continue
        with open(probe_file) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split()
                t = float(parts[0])
                if t <= last_time:
                    continue
                times.append(t)
                vals.append(float(parts[ceiling_idx + 1]))
                last_time = t

    if not times:
        return None, None, None
    return np.array(times), mass_to_vol_frac(np.array(vals)), ceiling_z


def main():
    parser = argparse.ArgumentParser(
        description="Grid sensitivity: ceiling H2 time history for fine vs coarse mesh."
    )
    parser.add_argument("case_fine",   type=int, help="Fine mesh case number")
    parser.add_argument("case_coarse", type=int, help="Coarse mesh case number")
    parser.add_argument("--xlim", type=float, default=30,
                        help="Upper x-axis limit in seconds (default: 30)")
    parser.add_argument("--exp", type=float, default=None,
                        help="Experimental ceiling H2 reference [vol%%] (omit to suppress)")
    args = parser.parse_args()

    cases  = [args.case_fine, args.case_coarse]
    labels = ["Fine mesh", "Coarse mesh"]
    colors = ["black", "red"]
    lss    = ["-", "--"]

    apply_style()
    fig, ax = plt.subplots(figsize=(GOLDEN_WIDTH, GOLDEN_HEIGHT))

    print(f"\nCeiling H2 summary (back-wall probes, highest z):")

    for case_num, label, color, ls in zip(cases, labels, colors, lss):
        times, ceiling, ceiling_z = read_ceiling_probe(case_num)
        if times is None:
            print(f"  Case {case_num}: no data found, skipping")
            continue
        z_str = f", z={ceiling_z:.3f} m" if ceiling_z is not None else ""
        mask = times <= args.xlim
        ax.plot(times[mask], ceiling[mask], color=color, linestyle=ls,
                linewidth=LW, label=label)
        last_val = ceiling[mask][-1] if mask.any() else float("nan")
        print(f"  Case {case_num} ({label}){z_str}: t={times[mask][-1]:.1f} s, "
              f"ceiling H2 = {last_val:.2f} vol%")

    if args.exp is not None:
        ax.axhline(args.exp, color="black", linestyle="-.", linewidth=LW,
                   label=f"Experiment = {args.exp:.2f} vol%")

    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Ceiling H$_2$ concentration [vol%]")
    ax.legend()
    ax.set_xlim(0, args.xlim)
    ax.set_ylim(bottom=0)

    plt.tight_layout()
    out_base = os.path.join(os.path.dirname(__file__),
                            f"grid_sensitivity_case{cases[0]}_vs_{cases[1]}")
    save_figure(fig, out_base)
    plt.show()


if __name__ == "__main__":
    main()
