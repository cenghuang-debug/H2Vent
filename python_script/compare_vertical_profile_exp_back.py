"""
compare_vertical_profile_exp_back.py — CFD vs experiment: vertical H2 profile.

Reads the vertical probe array for a given case, converts mass fraction to
volume fraction, and overlays the experimental data from Bernard-Michel &
Houssin-Agbomson 2017.

Probe set used:
    1 m³ cases  → probes_H2_vertical      (centre mast)
    2 m³ cases  → probes_H2_vertical_back (back-wall mast, opposite to vents,
                                           matching experimental sensor placement)

When target times are supplied, one CFD profile is plotted per time instance
(nearest available time step used). Without target times, only the last
available time step is plotted.

Usage:
    python3 compare_vertical_profile_exp_back.py [case_number] [t1 t2 t3 ...]
    e.g.:
        python3 compare_vertical_profile_exp_back.py 44              # latest time
        python3 compare_vertical_profile_exp_back.py 44 25 28 30 32  # four snapshots
"""

import numpy as np
import matplotlib.pyplot as plt
import os
import sys
import re

sys.path.insert(0, os.path.dirname(__file__))
from plot_style import apply_style, GOLDEN_HEIGHT, GOLDEN_WIDTH, LW, MS, MEW, MFCOLOR, save_figure

# ── constants ────────────────────────────────────────────────────────────────
M_H2  = 0.002016   # kg/mol
M_air = 0.028970   # kg/mol

CASE_PARAMS = {
    # 1 m³, 27 mm
    21: (218.1, 27, 1), 22: (104.0, 27, 1), 23: (62.4,  27, 1),
    24: ( 20.8, 27, 1), 25: ( 10.4, 27, 1),
    26: (218.1, 27, 1), 27: (218.1, 27, 1), 28: (218.1, 27, 1),
    29: (218.1, 27, 1), 30: (218.1, 27, 1), 31: (218.1, 27, 1),
    32: (218.1, 27, 1),
    68: (104.0, 27, 1), 69: ( 62.4, 27, 1), 70: ( 20.8, 27, 1), 71: ( 10.4, 27, 1),
    # 1 m³, 4 mm
    33: (218.1,  4, 1), 34: (104.0,  4, 1), 35: ( 62.4,  4, 1),
    36: ( 20.8,  4, 1), 38: ( 10.4,  4, 1), 39: (218.1,  4, 1),
    40: (218.1,  4, 1), 41: ( 10.4,  4, 1),
    64: (104.0,  4, 1), 65: ( 62.4,  4, 1), 66: ( 20.8,  4, 1),
    67: ( 10.4,  4, 1),
    # 2 m³, 4 mm
    42: (218.1,  4, 2), 43: (  5.2,  4, 2),
    72: (218.1,  4, 2),
    49: (  5.2,  4, 2), 50: (  5.2,  4, 2),
    61: ( 73.0,  4, 2), 62: ( 20.8,  4, 2), 63: (  5.2,  4, 2),
    # 2 m³, 27 mm
    44: (218.1, 27, 2), 45: (  5.2, 27, 2),
    46: (218.1, 27, 2), 47: ( 73.0, 27, 2), 48: ( 20.8, 27, 2),
    56: (218.1, 27, 2),
    58: ( 73.0, 27, 2), 59: ( 20.8, 27, 2), 60: (  5.2, 27, 2),
}

# Maps (vol_m3, nozzle_mm, q_NL_min) → experimental CSV filename
EXP_CSV_MAP = {
    (2, 27, 218.1): "H2_2m3_27mm_218NL_min.csv",
    (2, 27,  73.0): "H2_2m3_27mm_73NL_min.csv",
    (2,  4, 218.1): "H2_2m3_4mm_218NL_min.csv",
}

BASE_DIR    = os.path.join(os.path.dirname(__file__), "..")
EXP_DIR     = os.path.join(BASE_DIR, "experimental_data_Bernard-Michel")


# ── helpers ──────────────────────────────────────────────────────────────────
def mass_to_vol_frac(Y):
    X = (Y / M_H2) / (Y / M_H2 + (1.0 - Y) / M_air)
    return X * 100.0


def find_case_dir(case_num):
    for vol in (1, 2):
        for nozzle in (4, 27):
            d = os.path.join(BASE_DIR, f"{vol}m3_{nozzle}mm_wall_H2_test_{case_num:02d}")
            if os.path.isdir(d):
                return d, vol, nozzle
    return None, None, None


def read_probe_positions(probe_file):
    z_coords = []
    with open(probe_file) as f:
        for line in f:
            if not line.startswith("#"):
                break
            m = re.match(
                r"#\s*Probe\s+\d+\s+\([\d.e+\-]+\s+[\d.e+\-]+\s+([\d.e+\-]+)\)",
                line
            )
            if m:
                z_coords.append(float(m.group(1)))
    return z_coords


def _load_all_rows(probe_dir):
    """Load all time rows from all restart subfolders; return (z_coords, times, rows)."""
    time_folders = sorted(
        [d for d in os.listdir(probe_dir) if d.replace(".", "", 1).isdigit()],
        key=lambda x: float(x)
    )
    if not time_folders:
        return None, [], []

    first_file = os.path.join(probe_dir, time_folders[0], "H2")
    z_coords   = read_probe_positions(first_file)

    times = []
    rows  = []
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
                times.append(float(vals[0]))
                rows.append([float(v) for v in vals[1:]])

    return z_coords, np.array(times), rows


def read_profile_at_time(probe_dir, target_t):
    """Return (t_actual, z_coords [m], vol_frac [%]) at the time step nearest target_t."""
    z_coords, times, rows = _load_all_rows(probe_dir)
    if z_coords is None or len(times) == 0:
        return None, None, None
    idx      = int(np.argmin(np.abs(times - target_t)))
    t_actual = times[idx]
    return t_actual, z_coords, mass_to_vol_frac(np.array(rows[idx]))


def read_latest_profile(probe_dir):
    """Return (t_end, z_coords [m], vol_frac [%]) at the last available time step."""
    z_coords, times, rows = _load_all_rows(probe_dir)
    if z_coords is None or len(times) == 0:
        return None, None, None
    return times[-1], z_coords, mass_to_vol_frac(np.array(rows[-1]))


def read_experimental(csv_path):
    """Parse Plot Digitizer CSV; return (z_m, vol_pct) arrays."""
    z_cm_list  = []
    vol_pct_list = []
    in_data = False
    with open(csv_path) as f:
        for line in f:
            line = line.strip().strip('"')
            if not line:
                continue
            if line.startswith("vertical_pos_cm"):
                in_data = True
                continue
            if not in_data:
                continue
            parts = [p.strip() for p in line.split(",") if p.strip()]
            if len(parts) >= 2:
                try:
                    z_cm_list.append(float(parts[0]))
                    vol_pct_list.append(float(parts[1]))
                except ValueError:
                    continue
    return np.array(z_cm_list) / 100.0, np.array(vol_pct_list)


# ── argument parsing ─────────────────────────────────────────────────────────
args = sys.argv[1:]
case_num     = int(args[0]) if args else 44
target_times = [float(a) for a in args[1:]] if len(args) > 1 else []

# ── case setup ───────────────────────────────────────────────────────────────
case_dir, vol_m3, nozzle_mm = find_case_dir(case_num)
if case_dir is None:
    sys.exit(f"ERROR: case directory not found for case {case_num}")

params = CASE_PARAMS.get(case_num)
if params is None:
    sys.exit(f"ERROR: case {case_num} not in CASE_PARAMS — add it first")
q_NL = params[0]

probe_name = "probes_H2_vertical_back" if vol_m3 == 2 else "probes_H2_vertical"
probe_dir  = os.path.join(case_dir, "postProcessing", probe_name)
if not os.path.isdir(probe_dir):
    sys.exit(f"ERROR: {probe_name} not found in {case_dir}")

# Build list of (t_actual, z, vol_frac) snapshots to plot
if target_times:
    snapshots = []
    for t_req in target_times:
        t_actual, z_cfd, vol_cfd = read_profile_at_time(probe_dir, t_req)
        if t_actual is None:
            print(f"[WARNING] no data found near t={t_req} s, skipping.")
            continue
        snapshots.append((t_actual, z_cfd, vol_cfd))
        print(f"  t={t_req} s → nearest t={t_actual:.2f} s  |  ceiling H2 = {vol_cfd[np.argmax(z_cfd)]:.2f} vol%")
else:
    t_end, z_cfd, vol_cfd = read_latest_profile(probe_dir)
    if t_end is None:
        sys.exit("ERROR: no probe data found")
    snapshots = [(t_end, z_cfd, vol_cfd)]
    print(f"Case {case_num}: t={t_end:.1f} s  |  ceiling H2 = {vol_cfd[np.argmax(z_cfd)]:.2f} vol%")

# ── experimental data ────────────────────────────────────────────────────────
exp_key = (vol_m3, nozzle_mm, q_NL)
if exp_key not in EXP_CSV_MAP:
    sys.exit(
        f"ERROR: no experimental CSV mapped for (vol={vol_m3} m³, "
        f"nozzle={nozzle_mm} mm, Q={q_NL} NL/min)"
    )
exp_csv = os.path.join(EXP_DIR, EXP_CSV_MAP[exp_key])
if not os.path.exists(exp_csv):
    sys.exit(f"ERROR: experimental file not found: {exp_csv}")

z_exp, vol_exp = read_experimental(exp_csv)
print(f"Experiment: {len(z_exp)} points loaded from {os.path.basename(exp_csv)}")

# ── plot ─────────────────────────────────────────────────────────────────────
apply_style()
fig, ax = plt.subplots(figsize=(GOLDEN_HEIGHT, GOLDEN_WIDTH))   # portrait: narrow & tall

# Experimental: black filled circles connected by solid black line
ax.plot(
    vol_exp, z_exp,
    "o-", color="black",
    linewidth=LW, markersize=MS * 0.8, markeredgewidth=MEW,
    markerfacecolor="black",
    label="Experiment",
    zorder=4,
)

# CFD snapshots: square markers, red dashed lines, colour-mapped by time
n = len(snapshots)
if n == 1:
    cfd_colors = ["red"]
else:
    cmap = plt.cm.autumn_r          # dark red → orange, all warm tones
    cfd_colors = [cmap(i / (n - 1)) for i in range(n)]

for (t_actual, z_cfd, vol_cfd), color in zip(snapshots, cfd_colors):
    ax.plot(
        vol_cfd, z_cfd,
        "s--", color=color,
        linewidth=LW, markersize=MS * 0.8, markeredgewidth=MEW,
        markerfacecolor="none", markeredgecolor=color,
        label="Simulation",
        zorder=3,
    )

ax.set_xlabel("H$_2$ concentration [vol%]")
ax.set_ylabel("Height [m]")
ax.set_xlim(0, 7)
ax.set_ylim(bottom=0)

# Lower-right corner is empty (near-zero H2 at low z) — safe for legend
ax.legend(loc="lower right", fontsize=16)

plt.tight_layout()

# output filename encodes the requested times when supplied
if target_times:
    time_tag = "_".join(f"{t:.0f}" for t in target_times)
    out_base = os.path.join(
        os.path.dirname(__file__),
        f"vertical_profile_case{case_num:02d}_t{time_tag}_vs_exp"
    )
else:
    out_base = os.path.join(
        os.path.dirname(__file__),
        f"vertical_profile_case{case_num:02d}_vs_exp"
    )
save_figure(fig, out_base)
plt.show()
