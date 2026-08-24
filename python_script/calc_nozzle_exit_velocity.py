"""
Calculate H2 nozzle exit velocity, Reynolds number, and Richardson number
for all experimental flow rates.

Normal conditions: 0 degC (273.15 K), 101325 Pa  — defines NL/min
Injection temperature: 286.15 K (13 degC)
Isobaric ideal-gas correction:
  Q_inject = Q_N * (T_inject / T_normal)
  U_inject = Q_inject / A_nozzle
Mass flow rate mdot = rho_H2_normal * Q_N  (temperature-independent)

Reynolds number (nozzle-based, H2 properties at injection conditions):
  Re = rho_H2_inj * U_inj * D / mu_H2_inj

Richardson number (densimetric, nozzle-based):
  Ri = g * D * (rho_air - rho_H2_inj) / (rho_H2_inj * U_inj^2)
  Ri < 1: momentum-dominated jet; Ri > 1: buoyancy-dominated

Sutherland viscosity for H2 (White 2006, Table 1-2):
  mu = As * sqrt(T) / (1 + Ts/T),  As = 6.897e-7, Ts = 97 K

Output: printed per-enclosure tables + combined pivot table + two CSVs
"""

import math
import csv
import os
import pandas as pd

# ── Physical constants ───────────────────────────────────────────────────────
T_normal  = 273.15    # K  (0 degC, defines NL/min)
T_inject  = 286.15    # K  (actual injection temperature)
P_atm     = 101325.0  # Pa
R_univ    = 8.314     # J/(mol·K)
g         = 9.81      # m/s²
rho_H2    = 0.0899    # kg/m3  (H2 at normal conditions)
T_ratio   = T_inject / T_normal

# H2 Sutherland coefficients (White 2006, Table 1-2; As corrected for OF form)
As_H2 = 6.897e-7     # Pa·s·K^-0.5
Ts_H2 = 97.0         # K

# Derived quantities at injection temperature
M_H2      = 2.01588e-3   # kg/mol
M_air     = 28.964e-3    # kg/mol
rho_H2_inj  = rho_H2 * T_normal / T_inject          # ideal-gas correction
rho_air_inj = P_atm * M_air / (R_univ * T_inject)   # air at injection T
mu_H2_inj   = As_H2 * math.sqrt(T_inject) / (1.0 + Ts_H2 / T_inject)

# ── Test matrix ──────────────────────────────────────────────────────────────
cases = {
    1: [218.1, 104.0, 62.4, 20.8, 10.4],   # NL/min, 1 m3 enclosure
    2: [218.1,  73.0, 20.8,  5.2],          # NL/min, 2 m3 enclosure
}
diameters_mm = [4.0, 27]
areas = {D: math.pi * (D * 1e-3) ** 2 / 4 for D in diameters_mm}

# ── Build long-format result rows ────────────────────────────────────────────
rows = []
for vol, Q_list in cases.items():
    for D in diameters_mm:
        A = areas[D]
        for Q in Q_list:
            Q_m3s = Q / 60.0 / 1000.0
            U_N   = Q_m3s / A
            U_inj = U_N * T_ratio
            mdot  = rho_H2 * Q_m3s
            Re    = rho_H2_inj * U_inj * (D * 1e-3) / mu_H2_inj
            Ri    = g * (D * 1e-3) * (rho_air_inj - rho_H2_inj) / (rho_H2_inj * U_inj ** 2)
            rows.append({
                "enclosure_volume_m3": vol,
                "nozzle_diameter_mm":  D,
                "Q_N_NL_per_min":      Q,
                "Q_N_m3_per_s":        Q_m3s,
                "U_normal_m_per_s":    U_N,
                "U_inject_m_per_s":    U_inj,
                "mdot_kg_per_s":       mdot,
                "Re":                  Re,
                "Ri":                  Ri,
            })

script_dir = os.path.dirname(os.path.abspath(__file__))

# ── Save long-format CSV ─────────────────────────────────────────────────────
def fmt(val, col):
    if col in ("U_normal_m_per_s", "U_inject_m_per_s"):
        return f"{val:.2f}"
    if col in ("Q_N_m3_per_s", "mdot_kg_per_s"):
        return f"{val:.2e}"
    if col == "Re":
        return f"{val:.0f}"
    if col == "Ri":
        return f"{val:.3f}"
    return val

fieldnames = [
    "enclosure_volume_m3", "nozzle_diameter_mm", "Q_N_NL_per_min",
    "Q_N_m3_per_s", "U_normal_m_per_s", "U_inject_m_per_s", "mdot_kg_per_s",
    "Re", "Ri",
]
long_csv = os.path.join(script_dir, "H2_nozzle_exit_velocity_1m3_2m3.csv")
with open(long_csv, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow({col: fmt(row[col], col) for col in fieldnames})

# ── Build combined pivot table ───────────────────────────────────────────────
df = pd.DataFrame(rows)

# All unique Q_N values across both enclosures, sorted descending
all_Q = sorted(df["Q_N_NL_per_min"].unique(), reverse=True)

# mdot depends only on Q_N — take from any row for that Q
mdot_map = (
    df.drop_duplicates("Q_N_NL_per_min")
      .set_index("Q_N_NL_per_min")["mdot_kg_per_s"]
)

pivot_rows = []
for Q in all_Q:
    rec = {"Q_N [NL/min]": Q, "mdot [kg/s]": f"{mdot_map[Q]:.2e}"}
    for vol in [1, 2]:
        for D in diameters_mm:
            subset = df[(df["enclosure_volume_m3"] == vol) &
                        (df["nozzle_diameter_mm"] == D) &
                        (df["Q_N_NL_per_min"] == Q)]
            if len(subset):
                rec[f"U_inj {vol}m³ D={D}mm [m/s]"] = f"{subset['U_inject_m_per_s'].values[0]:.2f}"
                rec[f"Re {vol}m³ D={D}mm"]           = f"{subset['Re'].values[0]:.0f}"
                rec[f"Ri {vol}m³ D={D}mm"]           = f"{subset['Ri'].values[0]:.3f}"
            else:
                rec[f"U_inj {vol}m³ D={D}mm [m/s]"] = "—"
                rec[f"Re {vol}m³ D={D}mm"]           = "—"
                rec[f"Ri {vol}m³ D={D}mm"]           = "—"
    pivot_rows.append(rec)

pivot_df = pd.DataFrame(pivot_rows)

# ── Print combined table ─────────────────────────────────────────────────────
print("H2 nozzle exit velocity, Re, Ri — combined table")
print(f"  T_inject = {T_inject} K ({T_inject - 273.15:.0f} °C)  |  "
      f"T_ratio = T_inject/T_normal = {T_ratio:.4f}")
print(f"  rho_H2_inj  = {rho_H2_inj:.4f} kg/m³  |  "
      f"rho_air_inj = {rho_air_inj:.4f} kg/m³  |  "
      f"mu_H2_inj = {mu_H2_inj:.3e} Pa·s")
print(f"  Re = rho_H2_inj * U_inj * D / mu_H2_inj")
print(f"  Ri = g * D * (rho_air - rho_H2_inj) / (rho_H2_inj * U_inj²)  "
      f"[Ri<1: momentum-dominated, Ri>1: buoyancy-dominated]")
print()
print(pivot_df.to_string(index=False))
print()

# ── Save combined pivot as Excel ─────────────────────────────────────────────
xlsx_path = os.path.join(script_dir, "H2_nozzle_exit_velocity_combined.xlsx")
with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
    pivot_df.to_excel(writer, index=False, sheet_name="combined")

print(f"  Long-format CSV : {long_csv}")
print(f"  Combined Excel  : {xlsx_path}")
