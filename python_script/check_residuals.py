"""
check_residuals.py — Plot solver residuals (initial) vs time for a given case.

Stitches postProcessing/myResiduals subfolders across restarts automatically.
Auto-detects enclosure volume (1 m³ / 2 m³) and nozzle size (4 mm / 27 mm).
Parses the solverInfo header dynamically so it works across different case
configurations (with/without U, p_rgh, omega, etc.).

Reads system/fvSolution residualControl tolerances; annotates each field's
line with its tolerance (dotted reference line, same colour) and prints a
per-field convergence summary table.

Usage:
    python3 check_residuals.py <case_number>
    e.g.: python3 check_residuals.py 43
          python3 check_residuals.py 26
"""

import os
import re
import sys
import numpy as np
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(__file__))
from plot_style import apply_style, GOLDEN_WIDTH, GOLDEN_HEIGHT, LW, save_figure

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")


def find_case_dir(case_num):
    for vol in (1, 2):
        for nozzle in (4, 27):
            d = os.path.join(BASE_DIR, f"{vol}m3_{nozzle}mm_wall_H2_test_{case_num:02d}")
            if os.path.isdir(d):
                return d, vol, nozzle
    return None, None, None


def load_residuals(case_dir):
    """Stitch all myResiduals subfolders; return (header_list, float_array) sorted by time."""
    res_base = os.path.join(case_dir, "postProcessing", "myResiduals")
    if not os.path.isdir(res_base):
        print(f"ERROR: postProcessing/myResiduals not found in {case_dir}")
        sys.exit(1)

    segments = sorted(os.listdir(res_base), key=lambda x: float(x))
    header = None
    blocks = []

    for seg in segments:
        fpath = os.path.join(res_base, seg, "solverInfo.dat")
        if not os.path.isfile(fpath):
            continue
        rows = []
        with open(fpath) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if line.startswith("#"):
                    if header is None and "Time" in line:
                        header = line.lstrip("# ").split()
                    continue
                rows.append(line.split())
        if rows:
            blocks.append(rows)

    if not blocks or header is None:
        print("ERROR: no data or header found in myResiduals")
        sys.exit(1)

    all_rows = [r for block in blocks for r in block]
    # Keep only rows with the expected number of columns
    n_cols = len(header)
    all_rows = [r for r in all_rows if len(r) == n_cols]

    arr = np.array(all_rows)
    times = arr[:, 0].astype(float)
    order = np.argsort(times)
    return header, arr[order]


def get_col(header, arr, name):
    """Return column as float array by header name, or None if not present."""
    if name in header:
        return arr[:, header.index(name)].astype(float)
    return None


def parse_fvsolution_tolerances(case_dir):
    """Return {field_pattern: tolerance} from PIMPLE residualControl in system/fvSolution."""
    fvsol_path = os.path.join(case_dir, "system", "fvSolution")
    if not os.path.isfile(fvsol_path):
        return {}
    with open(fvsol_path) as f:
        content = f.read()

    rc_match = re.search(r'residualControl\s*\{', content)
    if not rc_match:
        return {}

    # Extract block by counting braces (handles nested sub-dicts per field)
    start = rc_match.end() - 1
    depth, end = 0, start
    for i, ch in enumerate(content[start:], start):
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                end = i
                break

    rc_block = content[start + 1:end]
    tolerances = {}
    for m in re.finditer(r'"?([^"\s{]+)"?\s*\{([^}]*)\}', rc_block, re.DOTALL):
        field_name = m.group(1)
        tol_m = re.search(r'tolerance\s+([\d.e+\-]+)', m.group(2))
        if tol_m:
            tolerances[field_name] = float(tol_m.group(1))
    return tolerances


def lookup_tolerance(tolerances, rc_field):
    """Exact match first, then treat dict keys as regex patterns (e.g. '(H2|O2|H2O|air)')."""
    if rc_field is None or not tolerances:
        return None
    if rc_field in tolerances:
        return tolerances[rc_field]
    for pattern, tol in tolerances.items():
        try:
            if re.fullmatch(pattern, rc_field):
                return tol
        except re.error:
            pass
    return None


# (label, [solverInfo columns to take max of], line colour, fvSolution residualControl field)
#
# p_rgh_initial is ~0.05 at every timestep (dominated by the reset between steps,
# not a PIMPLE convergence indicator).  p_rgh_final reflects linear-solver quality.
# PIMPLE residualControl checks the per-outer-iteration initial residual, which is
# not directly stored in solverInfo.dat — the p_rgh row is therefore annotated below.
FIELD_SPECS = [
    ("p_rgh",   ["p_rgh_final"],                           "#ff7f00", "p_rgh"),
    ("U",       ["Ux_initial", "Uy_initial", "Uz_initial"], "#377eb8", "U"),
    ("H2",      ["H2_initial"],                            "#4daf4a", "H2"),
    ("k",       ["k_initial"],                             "#984ea3", "k"),
    ("epsilon", ["epsilon_initial"],                       "#a65628", "epsilon"),
    ("omega",   ["omega_initial"],                         "#f781bf", "omega"),
    ("h",       ["h_initial"],                             "#999999", "h"),
]


def main():
    case_num = int(sys.argv[1]) if len(sys.argv) > 1 else 26

    case_dir, vol_m3, nozzle_mm = find_case_dir(case_num)
    if case_dir is None:
        print(f"ERROR: no case directory found for case {case_num}")
        sys.exit(1)

    print(f"Case {case_num}: {vol_m3} m³, {nozzle_mm} mm nozzle — {case_dir}")

    header, data = load_residuals(case_dir)
    t = data[:, 0].astype(float)
    tolerances = parse_fvsolution_tolerances(case_dir)

    if tolerances:
        print("residualControl tolerances read from system/fvSolution:")
        for field, tol in tolerances.items():
            print(f"  {field}: {tol:.1e}")
    else:
        print("WARNING: could not parse residualControl from system/fvSolution")

    apply_style()
    fig, ax = plt.subplots(figsize=(GOLDEN_WIDTH, GOLDEN_HEIGHT))

    plotted_fields = []
    for label, candidates, color, rc_field in FIELD_SPECS:
        cols = [get_col(header, data, c) for c in candidates if c in header]
        if not cols:
            continue
        values = np.maximum.reduce(cols) if len(cols) > 1 else cols[0]
        tol = lookup_tolerance(tolerances, rc_field)
        tol_str = f"{tol:.0e}" if tol is not None else "—"
        ax.semilogy(t, values, label=f"{label}  [tol={tol_str}]", color=color, linewidth=LW - 1)
        if tol is not None:
            # Dotted reference line at this field's tolerance, same colour
            ax.axhline(tol, color=color, linestyle=":", linewidth=1.4, alpha=0.75)
        plotted_fields.append((label, rc_field, color, tol, values))

    if not plotted_fields:
        print("ERROR: no recognised residual columns found")
        sys.exit(1)

    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Residual")
    ax.set_title(f"Case {case_num} — {vol_m3} m³, {nozzle_mm} mm nozzle\nSolver residuals  (dotted lines = PIMPLE residualControl tolerance)")
    ax.legend(loc="upper right", fontsize=12, ncol=2)
    ax.set_xlim(left=0)

    # ── Convergence summary table ────────────────────────────────────────────
    last_t = t[-1]
    n_avg = min(50, len(t))
    print(f"\nConvergence summary  (last {n_avg}-step average,  t_end = {last_t:.4g} s):")
    print(f"  {'Field':<10} {'RC Tolerance':>14} {'Avg Residual':>14} {'Status':>10}")
    print(f"  {'-'*10} {'-'*14} {'-'*14} {'-'*10}")
    for label, rc_field, color, tol, values in plotted_fields:
        avg_val = float(np.mean(values[-n_avg:]))
        if label == "p_rgh":
            # p_rgh_final (plotted) is the linear-solver exit residual (~1e-7).
            # PIMPLE residualControl checks the Initial residual of the first p_rgh
            # solve at the start of each outer iteration — that value is NOT stored
            # in solverInfo.dat, so convergence status cannot be determined here.
            print(f"  {label:<10} {tol:>14.1e} {avg_val:>14.3e} {'(see note)':>10}")
        elif tol is not None:
            status = "CONVERGED" if avg_val <= tol else "NOT CONV"
            print(f"  {label:<10} {tol:>14.1e} {avg_val:>14.3e} {status:>10}")
        else:
            print(f"  {label:<10} {'(no RC tol)':>14} {avg_val:>14.3e} {'N/A':>10}")
    print("  Notes:")
    print("  * solverInfo.dat records residuals from the FIRST outer iteration only.")
    print("    PIMPLE residualControl checks residuals after the LAST outer iteration,")
    print("    by which point they are much lower — 'NOT CONV' here does not mean the")
    print("    simulation is diverging; it means outer-iter-1 residuals exceed tolerance.")
    print("  * p_rgh: solverInfo stores p_rgh_final (linear-solver exit residual ~1e-7).")
    print("    PIMPLE checks the Initial residual of the first p_rgh solve per outer")
    print("    iteration; that value is not in solverInfo.dat — parse the log to verify.")

    out = os.path.join(os.path.dirname(__file__), f"residuals_case{case_num:02d}")
    save_figure(fig, out)
    plt.show()
    plt.close(fig)


if __name__ == "__main__":
    main()
