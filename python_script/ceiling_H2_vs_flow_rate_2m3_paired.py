"""
Ceiling H2 concentration vs flow rate — 2 m³ enclosure, 27 mm vs 4 mm nozzle.
CFD (rhoReactingBuoyantFoam) vs Bernard-Michel & Houssin-Agbomson 2017.

Both nozzles use the back-wall mast (probes_H2_vertical_back, opposite to vents),
matching the experimental sensor placement in Bernard-Michel Fig. 2.
Ceiling probe auto-detected as the probe at maximum z.
Time-averaged over the last 5 s of available data.
"""

import numpy as np
import matplotlib.pyplot as plt
import os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from plot_style import apply_style, GOLDEN_WIDTH, GOLDEN_HEIGHT, LW, MS, MEW, MFCOLOR, save_figure

M_H2  = 0.002016
M_air = 0.028970
T_AVG_WINDOW = 5.0
BASE_DIR = os.path.join(os.path.dirname(__file__), "..")

# ── case configurations ───────────────────────────────────────────────────────
CASES_27MM = {56: 218.1, 58: 73.0, 59: 20.8, 60: 5.2}
CASES_4MM  = {72: 218.1, 73: 73.0, 74: 20.8, 75: 5.2}

# Per-case fixed averaging centre (s); uses T_AVG_WINDOW around it instead of last 5 s.
# Case 75: ceiling H2 fluctuates — use a stable window around t=440 s.
CASE_T_CENTER = {75: 480.0}

# ── experimental data (Bernard-Michel & Houssin-Agbomson 2017) ────────────────
EXP_27MM_FLOW = np.array([218.1, 73.0, 20.8, 5.2])
EXP_27MM_CMAX = np.array([  6.17, 3.35, 1.83, 1.06])

EXP_4MM_FLOW  = np.array([218.1, 73.0, 20.8, 5.2])
EXP_4MM_CMAX  = np.array([  5.44, 3.30, 1.73, 1.09])

# ── helpers ───────────────────────────────────────────────────────────────────
def mass_to_vol_frac(Y):
    X = (Y / M_H2) / (Y / M_H2 + (1.0 - Y) / M_air)
    return X * 100.0

def read_probe_positions(probe_file):
    z_coords = []
    with open(probe_file) as f:
        for line in f:
            if not line.startswith("#"):
                break
            m = re.match(
                r"#\s*Probe\s+\d+\s+\([\d.e+\-]+\s+[\d.e+\-]+\s+([\d.e+\-]+)\)", line
            )
            if m:
                z_coords.append(float(m.group(1)))
    return z_coords

def read_probe_data(probe_dir):
    time_folders = sorted(
        [d for d in os.listdir(probe_dir) if d.replace(".", "", 1).isdigit()],
        key=lambda x: float(x)
    )
    if not time_folders:
        return None, None, None
    first_file = os.path.join(probe_dir, time_folders[0], "H2")
    z_coords    = read_probe_positions(first_file)
    ceiling_idx = int(np.argmax(z_coords)) if z_coords else 0
    times, data, last_time = [], [], -1.0
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
    return np.array(times), np.array(data), ceiling_idx

def avg_ceiling(times, data, col_idx, t_center=None):
    if t_center is not None:
        half    = T_AVG_WINDOW / 2.0
        t_start = t_center - half
        t_end   = t_center + half
        mask    = (times >= t_start) & (times <= t_end)
    else:
        t_end   = times[-1]
        t_start = max(t_end - T_AVG_WINDOW, times[0])
        mask    = times >= t_start
    if mask.sum() == 0:
        mask = np.ones(len(times), dtype=bool)
    return mass_to_vol_frac(data[mask, col_idx]).mean(), t_start, t_end

def collect(cases, dir_pattern, exp_flow, exp_cmax, label):
    sim_flow, sim_Cmax = [], []
    print(f"\n{label}")
    print(f"{'Case':>6}  {'Q [NL/min]':>12}  {'Cmax_sim [%]':>14}  {'Cmax_exp [%]':>14}  {'Error':>8}")
    print("-" * 62)
    for case_num, q_NL in sorted(cases.items()):
        probe_dir = os.path.join(BASE_DIR, dir_pattern.format(case_num),
                                 "postProcessing", "probes_H2_vertical_back")
        if not os.path.isdir(probe_dir):
            print(f"  case {case_num}: not found, skipping.")
            continue
        times, data, ceiling_idx = read_probe_data(probe_dir)
        if times is None:
            print(f"  case {case_num}: no data, skipping.")
            continue
        Cmax_sim, t0, t1 = avg_ceiling(times, data, ceiling_idx,
                                       t_center=CASE_T_CENTER.get(case_num))
        Cmax_exp = exp_cmax[np.argmin(np.abs(exp_flow - q_NL))]
        sim_flow.append(q_NL)
        sim_Cmax.append(Cmax_sim)
        print(f"  {case_num:>4}  {q_NL:>12.1f}  {Cmax_sim:>14.2f}  "
              f"{Cmax_exp:>14.2f}  {Cmax_sim - Cmax_exp:>+8.2f}  (avg {t0:.0f}–{t1:.0f} s)")
    return sim_flow, sim_Cmax

# ── collect results ───────────────────────────────────────────────────────────
sim_27mm_flow, sim_27mm_Cmax = collect(
    CASES_27MM, "2m3_27mm_wall_H2_test_{:02d}", EXP_27MM_FLOW, EXP_27MM_CMAX,
    "2 m³, 27 mm nozzle")
sim_4mm_flow, sim_4mm_Cmax = collect(
    CASES_4MM, "2m3_4mm_wall_H2_test_{:02d}", EXP_4MM_FLOW, EXP_4MM_CMAX,
    "2 m³, 4 mm nozzle")

# ── plot ──────────────────────────────────────────────────────────────────────
apply_style()
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(GOLDEN_WIDTH * 2, GOLDEN_HEIGHT), sharey=True)

# left panel: 27 mm nozzle
ax1.plot(EXP_27MM_FLOW, EXP_27MM_CMAX, "o-",
         color="black", markerfacecolor="black",
         linewidth=LW, markersize=MS, markeredgewidth=MEW,
         label="Experiment")
if sim_27mm_flow:
    order = np.argsort(sim_27mm_flow)
    ax1.plot(np.array(sim_27mm_flow)[order], np.array(sim_27mm_Cmax)[order], "o--",
             color="red", markerfacecolor=MFCOLOR,
             linewidth=LW, markersize=MS, markeredgewidth=MEW,
             label="Simulation")
ax1.set_xlabel("H$_2$ flow rate [NL/min]")
ax1.set_ylabel("Ceiling H$_2$ concentration [vol%]")
ax1.set_title("(a) 27 mm nozzle")
ax1.legend()
ax1.set_xlim(0, 230)
ax1.set_ylim(0, 12)

# right panel: 4 mm nozzle
ax2.plot(EXP_4MM_FLOW, EXP_4MM_CMAX, "s-",
         color="black", markerfacecolor="black",
         linewidth=LW, markersize=MS, markeredgewidth=MEW,
         label="Experiment")
if sim_4mm_flow:
    order = np.argsort(sim_4mm_flow)
    ax2.plot(np.array(sim_4mm_flow)[order], np.array(sim_4mm_Cmax)[order], "s--",
             color="red", markerfacecolor=MFCOLOR,
             linewidth=LW, markersize=MS, markeredgewidth=MEW,
             label="Simulation")
ax2.set_xlabel("H$_2$ flow rate [NL/min]")
ax2.set_title("(b) 4 mm nozzle")
ax2.legend()
ax2.set_xlim(0, 230)

plt.tight_layout()
out_base = os.path.join(os.path.dirname(__file__), "ceiling_H2_vs_flow_rate_2m3_paired")
save_figure(fig, out_base)
plt.show()
