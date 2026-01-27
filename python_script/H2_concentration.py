import pandas as pd
import matplotlib.pyplot as plt
import os
from my_fig_format import set_my_fig_format
set_my_fig_format()                     # Applies your custom style (fonts, sizes, etc.)

# ========================== User Settings ==========================
folder_name = "1m3_27mm_wall_H2_test_51"
base_path   = r"H2Vent"   # change the path
probe_time  = "0"         # change if your probes are in folder "0", "100", etc.

# Molecular weights (kg/mol)
MW_H2  = 0.00201588
MW_air = 0.02897
# ==================================================================

# Build path and read only the H2 probe file
probe_dir = os.path.join(base_path, folder_name, "postProcessing", "probes_H2_vertical", probe_time)
h2_file   = os.path.join(probe_dir, "H2")

# ---- Read probe data ----
with open(h2_file) as f:
    lines = f.readlines()

data_start = next(i for i, line in enumerate(lines) if not line.strip().startswith('#'))
headers    = lines[data_start-1].replace('#', '').strip().split()

df = pd.read_csv(h2_file, delim_whitespace=True, comment='#', names=headers)

time = df["Time"]
probes = [col for col in df.columns if col != "Time"]

# ---- Mass → Mole (volume) fraction for H2-in-air ----
Y_H2 = df[probes].values                                   # mass fractions
X_H2 = (Y_H2 / MW_H2) / (Y_H2 / MW_H2 + (1 - Y_H2) / MW_air)   # mole fractions
df_mole = pd.DataFrame(X_H2, columns=probes, index=time)

# ========================== Plot ==========================
plt.figure()

for probe in probes:
    plt.plot(df_mole.index, df_mole[probe] * 100, label=f'Probe {probe}')

plt.xlabel("Time (s)")
plt.ylabel("H₂ concentration (vol% / mol%)")
plt.title(f"H₂ Mole Fraction vs Time – Vertical Probes\n{folder_name}")
plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left", borderaxespad=0)
plt.grid(True, alpha=0.3)
plt.xlim(left=0)
plt.ylim(bottom=0)

plt.tight_layout()

# Optional: automatically save next to the probe data
save_path = os.path.join(probe_dir, "H2_mole_fraction_vertical.png")
plt.savefig(save_path, dpi=300, bbox_inches="tight")
print(f"Plot saved to: {save_path}")

plt.show()
