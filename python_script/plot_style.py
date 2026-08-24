"""
plot_style.py — Publication-quality figure style template.

Usage in your plot script:
    from plot_style import apply_style, GOLDEN_WIDTH, GOLDEN_HEIGHT, LW, MS, MEW, MFCOLOR

    apply_style()
    fig, ax = plt.subplots(figsize=(GOLDEN_WIDTH, GOLDEN_HEIGHT))
"""

import matplotlib.pyplot as plt

# ── figure dimensions ────────────────────────────────────────────────────────
GOLDEN_RATIO  = 1.618
GOLDEN_WIDTH  = 9.0                      # inches (full journal column width)
GOLDEN_HEIGHT = GOLDEN_WIDTH / GOLDEN_RATIO   # ~5.56 inches

# ── line / marker style ──────────────────────────────────────────────────────
LW      = 3       # line width
MS      = 18      # marker size
MEW     = 3       # marker edge width
MFCOLOR = "none"        # marker face color — open (unfilled) simulation markers

# ── font size ────────────────────────────────────────────────────────────────
FONTSIZE = 20


def apply_style():
    """Apply publication-quality rcParams. Call once before creating any figure."""
    plt.rcParams.update({
        # font
        "font.size":              FONTSIZE,
        "axes.titlesize":         FONTSIZE,
        "axes.labelsize":         FONTSIZE,
        "xtick.labelsize":        FONTSIZE,
        "ytick.labelsize":        FONTSIZE,
        "legend.fontsize":        FONTSIZE,
        # ticks — inside, on all 4 sides, with minor ticks
        "xtick.direction":        "in",
        "ytick.direction":        "in",
        "xtick.minor.visible":    True,
        "ytick.minor.visible":    True,
        "xtick.major.size":       8,
        "xtick.minor.size":       4,
        "ytick.major.size":       8,
        "ytick.minor.size":       4,
        "xtick.top":              True,
        "ytick.right":            True,
        # lines
        "lines.linewidth":        LW,
        "lines.markersize":       MS,
        # grid
        "axes.grid":              True,
        "grid.linestyle":         "--",
        "grid.alpha":             0.5,
        # save
        "savefig.dpi":            300,
        "savefig.bbox":           "tight",
    })


def save_figure(fig, path_without_ext):
    """Save figure as PDF (vector, for LaTeX) and PNG (300 dpi, raster fallback)."""
    for ext in ("pdf", "png"):
        out = f"{path_without_ext}.{ext}"
        fig.savefig(out)
        print(f"Saved: {out}")
