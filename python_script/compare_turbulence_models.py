"""
compare_turbulence_models.py — Compare ceiling H2 time history across turbulence models.

Cases (all 218.1 NL/min, 1 m³, 27 mm nozzle, same mesh as case 26):
  26: kEpsilon (baseline)
  29: kOmegaSST
  30: realizableKE
  31: RNGkEpsilon

Usage:
    python3 compare_turbulence_models.py
"""

import numpy as np
import matplotlib.pyplot as plt
import os, sys

sys.path.insert(0, os.path.dirname(__file__))
from plot_style import apply_style, GOLDEN_WIDTH, GOLDEN_HEIGHT, LW, MS, MEW, save_figure

M_H2  = 0.002016
M_air = 0.028970

def mass_to_vol_frac(Y):
    X = (Y / M_H2) / (Y / M_H2 + (1.0 - Y) / M_air)
    return X * 100.0

CEILING_PROBE = 14
BASE_DIR = os.path.join(os.path.dirname(__file__), "..")

CASES = {
    26: ("k-$\\varepsilon$",     "red",   "--"),
    29: ("k-$\\omega$ SST",      "blue",  "-."),
    31: ("RNG k-$\\varepsilon$", "green", ":"),
}

EXP_CEILING = 11.12  # vol%, Bernard-Michel 2017
EXP_TIME    = 80.0   # s, approximate steady-state sampling time

def read_ceiling_probe(case_num):
    probe_dir = os.path.join(
        BASE_DIR,
        f"1m3_27mm_wall_H2_test_{case_num:02d}",
        "postProcessing", "probes_H2_vertical"
    )
    if not os.path.exists(probe_dir):
        return None, None

    time_folders = sorted(
        [d for d in os.listdir(probe_dir) if d.replace('.', '', 1).isdigit()],
        key=lambda x: float(x)
    )

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
                vals.append(float(parts[CEILING_PROBE + 1]))
                last_time = t

    return np.array(times), mass_to_vol_frac(np.array(vals))

# ── plot ────────────────────────────────────────────────────────────────────
apply_style()
fig, ax = plt.subplots(figsize=(GOLDEN_WIDTH, GOLDEN_HEIGHT))

for case_num, (label, color, ls) in CASES.items():
    times, ceiling = read_ceiling_probe(case_num)
    if times is None:
        print(f"  Case {case_num} ({label}): no data, skipping")
        continue
    ax.plot(times, ceiling, color=color, linestyle=ls, linewidth=LW, label=label)
    # print summary
    avg_last20 = ceiling[-min(200, len(ceiling)):].mean()
    print(f"  Case {case_num} ({label:20s}): t_end={times[-1]:.0f} s, "
          f"ceiling H2 (last 20s avg) = {avg_last20:.2f} vol%")

ax.plot(EXP_TIME, EXP_CEILING, marker="o", markersize=MS, markeredgewidth=MEW,
        markerfacecolor="black", markeredgecolor="black", linestyle="none",
        label="Experiment")

ax.set_xlabel("Time [s]")
ax.set_ylabel("Ceiling H$_2$ concentration [vol%]")
ax.legend()
ax.set_xlim(0)
ax.set_ylim(0, 15)

plt.tight_layout()
out_base = os.path.join(os.path.dirname(__file__), "turbulence_model_comparison")
save_figure(fig, out_base)
plt.show()
