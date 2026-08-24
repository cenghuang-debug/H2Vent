"""
plot_probes_timeseries.py — Plot all vertical H2 probes (vol%) vs time for any case.

Auto-detects enclosure volume (1 m³ / 2 m³) and nozzle size (4 mm / 27 mm) from
which case directory exists on disk.  Probe z-positions are read from the file
header — no hard-coding.

Usage:
    python3 plot_probes_timeseries.py <case_number>
    e.g.:
        python3 plot_probes_timeseries.py 26    # 1 m³, 27 mm
        python3 plot_probes_timeseries.py 40    # 1 m³, 4 mm
        python3 plot_probes_timeseries.py 42    # 2 m³, 4 mm
"""

import numpy as np
import matplotlib.pyplot as plt
import os, sys, re

sys.path.insert(0, os.path.dirname(__file__))
from plot_style import apply_style, GOLDEN_WIDTH, GOLDEN_HEIGHT, LW, save_figure

# ── constants ────────────────────────────────────────────────────────────────
M_H2  = 0.002016   # kg/mol
M_air = 0.028970   # kg/mol

def mass_to_vol_frac(Y):
    X = (Y / M_H2) / (Y / M_H2 + (1.0 - Y) / M_air)
    return X * 100.0

# ── case → (Q [NL/min], nozzle [mm], volume [m³]) ───────────────────────────
CASE_PARAMS = {
    # 1 m³, 27 mm
    21: (218.1, 27, 1), 22: (104.0, 27, 1), 23: (62.4,  27, 1),
    24: ( 20.8, 27, 1), 25: ( 10.4, 27, 1),
    26: (218.1, 27, 1), 27: (218.1, 27, 1), 28: (218.1, 27, 1),
    29: (218.1, 27, 1), 30: (218.1, 27, 1), 31: (218.1, 27, 1),
    32: (218.1, 27, 1), 55: (218.1, 27, 1),
    68: (104.0, 27, 1), 69: ( 62.4, 27, 1), 70: ( 20.8, 27, 1), 71: ( 10.4, 27, 1),
    # 1 m³, 4 mm
    33: (218.1,  4, 1), 34: (104.0,  4, 1), 35: ( 62.4,  4, 1),
    36: ( 20.8,  4, 1), 38: ( 10.4,  4, 1), 39: (218.1,  4, 1),
    40: (218.1,  4, 1), 41: ( 10.4,  4, 1), 54: (218.1,  4, 1),
    64: (104.0,  4, 1), 65: ( 62.4,  4, 1), 66: ( 20.8,  4, 1),
    67: ( 10.4,  4, 1),
    76: (218.1,  4, 1), 77: (104.0,  4, 1), 78: ( 62.4,  4, 1),
    79: ( 20.8,  4, 1), 80: ( 10.4,  4, 1),
    # 2 m³, 4 mm
    42: (218.1,  4, 2), 43: (  5.2,  4, 2), 44: (218.1,  4, 2),
    45: (  5.2,  4, 2), 57: (218.1,  4, 2),
    61: ( 73.0,  4, 2), 62: ( 20.8,  4, 2), 63: (  5.2,  4, 2),
    72: (218.1,  4, 2), 73: ( 73.0,  4, 2), 74: ( 20.8,  4, 2), 75: (  5.2,  4, 2),
    # 2 m³, 27 mm
    46: (218.1, 27, 2), 47: ( 73.0, 27, 2), 48: ( 20.8, 27, 2),
    49: (  5.2,  4, 2), 56: (218.1, 27, 2),
    50: (  5.2,  4, 2),
    60: (  5.2, 27, 2),
}

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
EXP_CSV  = os.path.join(BASE_DIR, "experimental_data_Bernard-Michel", "experimental_data.csv")
# ── auto-detect case directory ───────────────────────────────────────────────
def find_case_dir(case_num):
    """Try all volume/nozzle combinations and return (path, vol_m3, nozzle_mm)."""
    for vol in (1, 2):
        for nozzle in (4, 27):
            d = os.path.join(BASE_DIR, f"{vol}m3_{nozzle}mm_wall_H2_test_{case_num:02d}")
            if os.path.isdir(d):
                return d, vol, nozzle
    return None, None, None

# ── parse probe positions from H2 file header ────────────────────────────────
def read_probe_positions(probe_file):
    """Return list of z-coordinates [m] from '# Probe N (x y z)' header lines."""
    z_coords = []
    with open(probe_file) as f:
        for line in f:
            if not line.startswith("#"):
                break
            m = re.match(r"#\s*Probe\s+\d+\s+\([\d.e+-]+\s+[\d.e+-]+\s+([\d.e+-]+)\)", line)
            if m:
                z_coords.append(float(m.group(1)))
    return z_coords

# ── stitch probe data across restart subfolders ──────────────────────────────
def read_probe_data(probe_dir):
    time_folders = sorted(
        [d for d in os.listdir(probe_dir) if d.replace(".", "", 1).isdigit()],
        key=lambda x: float(x)
    )
    if not time_folders:
        return None, None, None

    # get z-positions from first folder
    first_file = os.path.join(probe_dir, time_folders[0], "H2")
    z_coords = read_probe_positions(first_file)

    times, data = [], []
    last_time = -1.0
    for folder in time_folders:
        fpath = os.path.join(probe_dir, folder, "H2")
        if not os.path.exists(fpath):
            continue
        with open(fpath) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                vals = line.split()
                t = float(vals[0])
                if t <= last_time:
                    continue
                times.append(t)
                data.append([float(v) for v in vals[1:]])
                last_time = t

    return np.array(times), np.array(data), z_coords

# ── load experimental ceiling value ─────────────────────────────────────────
def get_exp_ceiling(vol_m3, nozzle_mm, q_NL):
    if not os.path.isfile(EXP_CSV):
        return None
    with open(EXP_CSV) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("volume"):
                continue
            parts = line.split("\t")
            if len(parts) < 7:
                continue
            try:
                if (int(parts[0]) == vol_m3
                        and int(parts[1]) == nozzle_mm
                        and abs(float(parts[4]) - q_NL) < 0.5):
                    return float(parts[6].replace("%", ""))
            except (ValueError, IndexError):
                continue
    return None

# ── main ─────────────────────────────────────────────────────────────────────
case_num = int(sys.argv[1]) if len(sys.argv) > 1 else 26

case_dir, vol_m3, nozzle_mm = find_case_dir(case_num)
if case_dir is None:
    print(f"ERROR: no case directory found for case {case_num}.")
    sys.exit(1)

probe_dir = os.path.join(case_dir, "postProcessing", "probes_H2_vertical")
if not os.path.isdir(probe_dir):
    print(f"ERROR: postProcessing/probes_H2_vertical not found in {case_dir}")
    sys.exit(1)

times, data, z_coords = read_probe_data(probe_dir)
if times is None:
    print("ERROR: no probe data found.")
    sys.exit(1)

data_vol = mass_to_vol_frac(data)
n_probes = data_vol.shape[1]
ceiling_idx = int(np.argmax(z_coords)) if z_coords else n_probes - 1

# ── experimental value ───────────────────────────────────────────────────────
q_NL     = CASE_PARAMS.get(case_num, (None,))[0]
exp_val  = get_exp_ceiling(vol_m3, nozzle_mm, q_NL) if q_NL is not None else None

# ── plot ─────────────────────────────────────────────────────────────────────
apply_style()
fig, ax = plt.subplots(figsize=(GOLDEN_WIDTH, GOLDEN_HEIGHT))

cmap = plt.cm.viridis
colors = cmap(np.linspace(0, 1, n_probes))

for i in range(n_probes):
    z_label = f"z = {z_coords[i]:.3f} m" if z_coords else f"Probe {i}"
    lw = LW if i == ceiling_idx else 1.5
    ax.plot(times, data_vol[:, i], linewidth=lw, color=colors[i], label=z_label)

# experimental reference
if exp_val is not None:
    ax.axhline(exp_val, color="black", linestyle="-.", linewidth=LW,
               label=f"Experiment = {exp_val:.2f} vol%")

q_str = f"{q_NL:.1f} NL/min" if q_NL else "unknown Q"
ax.set_xlabel("Time [s]")
ax.set_ylabel("H$_2$ concentration [vol%]")
ax.set_title(f"Case {case_num} — {vol_m3} m³, {nozzle_mm} mm nozzle, {q_str}\nVertical probes")
ax.legend(fontsize=11, loc="upper left")
ax.set_ylim(bottom=0)

plt.tight_layout()
out_base = os.path.join(os.path.dirname(__file__), f"probes_timeseries_case{case_num:02d}")
save_figure(fig, out_base)
plt.show()
