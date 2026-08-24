"""
check_probe_timeseries.py — Plot H2 ceiling probe (probe 14) time history for a given case.

Supports both 4 mm and 27 mm nozzle cases (1 m³ enclosure).
The nozzle size is auto-detected from which case directory exists on disk.

Usage:
    python3 check_probe_timeseries.py <case_number>
    e.g.: python3 check_probe_timeseries.py 24    # 27 mm nozzle
          python3 check_probe_timeseries.py 40    # 4 mm nozzle
"""

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

case_num = int(sys.argv[1]) if len(sys.argv) > 1 else 24

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")

# ── auto-detect nozzle size from which case directory exists ─────────────────
def find_case_dir(case_num):
    for nozzle in (27, 4):
        d = os.path.join(BASE_DIR, f"1m3_{nozzle}mm_wall_H2_test_{case_num:02d}")
        if os.path.isdir(d):
            return d, nozzle
    return None, None

case_dir, nozzle_mm = find_case_dir(case_num)
if case_dir is None:
    print(f"ERROR: no case directory found for case {case_num} (tried 4 mm and 27 mm).")
    sys.exit(1)

probe_dir = os.path.join(case_dir, "postProcessing", "probes_H2_vertical")

# ── map case number → (flow_rate [NL/min], nozzle [mm], volume [m³]) ─────────
_case_params = {
    # 27 mm nozzle cases
    21: (218.1, 27, 1), 22: (104.0, 27, 1), 23: (62.4, 27, 1),
    24: ( 20.8, 27, 1), 25: ( 10.4, 27, 1),
    26: (218.1, 27, 1), 27: (218.1, 27, 1), 28: (218.1, 27, 1),
    29: (218.1, 27, 1), 30: (218.1, 27, 1), 31: (218.1, 27, 1),
    32: (218.1, 27, 1),
    68: (104.0, 27, 1), 69: ( 62.4, 27, 1), 70: ( 20.8, 27, 1), 71: ( 10.4, 27, 1),
    # 4 mm nozzle cases — 1 m³
    33: (218.1,  4, 1),
    34: (104.0,  4, 1),
    35: ( 62.4,  4, 1),
    36: ( 20.8,  4, 1),
    38: ( 10.4,  4, 1),
    39: (218.1,  4, 1),
    40: (218.1,  4, 1),
    41: ( 10.4,  4, 1),
    64: (104.0,  4, 1),
    65: ( 62.4,  4, 1),
    66: ( 20.8,  4, 1),
    67: ( 10.4,  4, 1),
    # 2 m³ cases (find_case_dir searches 1m3_ only; params used for exp ref line)
    60: (  5.2, 27, 2),
    61: ( 73.0,  4, 2),
    62: ( 20.8,  4, 2),
    63: (  5.2,  4, 2),
}

# Collect all numeric time subfolders, sorted chronologically
time_folders = sorted(
    [d for d in os.listdir(probe_dir) if d.replace('.', '', 1).isdigit()],
    key=lambda x: float(x)
)

times, data = [], []
last_time = -1.0
for folder in time_folders:
    probe_file = os.path.join(probe_dir, folder, "H2")
    with open(probe_file) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            vals = line.split()
            t = float(vals[0])
            # skip duplicate/overlapping times from restart boundaries
            if t <= last_time:
                continue
            times.append(t)
            data.append([float(v) for v in vals[1:]])
            last_time = t

times = np.array(times)
data  = np.array(data)

# convert all probes to vol%
data_vol = mass_to_vol_frac(data)

apply_style()
fig, ax = plt.subplots(figsize=(GOLDEN_WIDTH, GOLDEN_HEIGHT))

# plot all probes, highlight probe 14 (ceiling)
for i in range(data_vol.shape[1]):
    if i == 14:
        ax.plot(times, data_vol[:, i], linewidth=LW, color="red", label="Probe 14 (z=0.95 m, ceiling)")
    else:
        ax.plot(times, data_vol[:, i], linewidth=1,  color="gray", alpha=0.4)

# shade averaging window: last 20 s of simulation
t_end = times[-1]
t_avg_start = max(t_end - 20.0, times[0])
mask_avg = times >= t_avg_start
mean_val = data_vol[mask_avg, 14].mean()
ax.axvspan(t_avg_start, t_end, alpha=0.12, color="blue",
           label=f"Averaging window ({t_avg_start:.0f}–{t_end:.0f} s)")
ax.axhline(mean_val, color="red", linestyle="--",
           linewidth=LW, label=f"CFD mean = {mean_val:.2f} vol%")

# ── experimental reference line from Bernard-Michel (2017) ───────────────────
exp_csv = os.path.join(BASE_DIR, "experimental_data_Bernard-Michel", "experimental_data.csv")
if case_num in _case_params and os.path.isfile(exp_csv):
    _q, _d, _v = _case_params[case_num]
    with open(exp_csv) as _f:
        for _line in _f:
            _line = _line.strip()
            if not _line or _line.startswith("volume"):
                continue
            _parts = _line.split("\t")
            if len(_parts) < 7:
                continue
            try:
                if (int(_parts[0]) == _v and int(_parts[1]) == _d
                        and abs(float(_parts[4]) - _q) < 0.5):
                    _exp_val = float(_parts[6].replace("%", ""))
                    ax.axhline(_exp_val, color="blue", linestyle="-.",
                               linewidth=LW, label=f"Experiment = {_exp_val:.2f} vol%")
                    break
            except (ValueError, IndexError):
                continue

case_label = os.path.basename(case_dir)
ax.set_xlabel("Time [s]")
ax.set_ylabel("H$_2$ concentration [vol%]")
ax.set_title(f"{case_label} — Vertical probes")
ax.legend(fontsize=14)
ax.set_xlim(0, times[-1])
ax.set_ylim(bottom=0)

plt.tight_layout()
out_base = os.path.join(os.path.dirname(__file__), f"probe_timeseries_case{case_num:02d}")
save_figure(fig, out_base)
plt.show()
