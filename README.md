# H2Vent — OpenFOAM Hydrogen Dispersion Validation Cases

OpenFOAM v2406 case setups, solver configurations, and post-processing scripts for:

> Huang, C., Dahlbom, S., Gehandler, J., Arymbayeva, A. *Benchmarking Hydrogen Dispersion CFD
> Simulations Using OpenFOAM.* Submitted to Process Safety and Environmental Protection /
> Journal of Loss Prevention in the Process Industries, 2026.

Hydrogen dispersion in naturally ventilated enclosures is simulated with the compressible,
buoyancy-driven, multi-species solver `rhoReactingBuoyantFoam` and validated against the
two-vent enclosure experiments of Bernard-Michel and Houssin-Agbomson (2017).

## Repository scope

This repository contains the **case setup and post-processing data** needed to reproduce the
results reported in the paper — mesh generation dictionaries, boundary conditions, solver
settings, and probe/residual time-series data. It does **not** include the full solved 3D field
results (velocity, pressure, species fields at every time step), which are large
(hundreds of MB to several GB per case) and are regenerable by running the solver from the
included case setup. See [Reproducing a case](#reproducing-a-case) below.

## Case directory naming

Directories follow `<enclosure>_<nozzle>_wall_H2_test_<N>`, e.g.
`1m3_27mm_wall_H2_test_55` = 1 m³ enclosure, 27 mm nozzle, internal test number 55.
The internal test numbers are not sequential by design parameter — they reflect the
chronological order cases were run during the study. The table below maps each included case
to its role in the paper.

### Validated cases — 1 m³ enclosure (Fig. 6)

| Case | Nozzle | Q [NL/min] |
|------|--------|-----------|
| 55 | 27 mm | 218.1 |
| 68 | 27 mm | 104.0 |
| 69 | 27 mm | 62.4  |
| 70 | 27 mm | 20.8  |
| 71 | 27 mm | 10.4  |
| 76 | 4 mm  | 218.1 |
| 77 | 4 mm  | 104.0 |
| 78 | 4 mm  | 62.4  |
| 79 | 4 mm  | 20.8  |
| 80 | 4 mm  | 10.4  |

### Validated cases — 2 m³ enclosure (Figs. 5, 9, 10)

| Case | Nozzle | Q [NL/min] |
|------|--------|-----------|
| 56 | 27 mm | 218.1 |
| 58 | 27 mm | 73.0  |
| 59 | 27 mm | 20.8  |
| 60 | 27 mm | 5.2   |
| 72 | 4 mm  | 218.1 |
| 73 | 4 mm  | 73.0  |
| 74 | 4 mm  | 20.8  |
| 75 | 4 mm  | 5.2   |

### Turbulence model sensitivity — 1 m³, 27 mm nozzle, 218.1 NL/min (Fig. 4)

| Case | Turbulence model |
|------|-----------------|
| 26 | standard k–ε |
| 29 | k–ω SST |
| 31 | RNG k–ε |

### Grid sensitivity — 2 m³, 4 mm nozzle, 73 NL/min (Fig. 3)

| Case | Mesh |
|------|------|
| 73 | Coarse (542,266 cells) — also the validated 2 m³/4 mm/73 NL/min case above |
| 61 | Fine (1,668,027 cells) |

## Repository contents

```
<case_dir>/
├── 0.orig/              # initial/boundary conditions (copied to 0/ by Allrun)
├── constant/             # mesh dictionaries, STL surfaces, thermophysical/turbulence properties
├── system/               # blockMesh, snappyHexMesh, fvSchemes, fvSolution, decomposeParDict, ...
├── Allrun / Allclean      # meshing workflow (blockMesh, snappyHexMesh, topoSet, createPatch, ...)
├── sbatch_OF_dardel_monitor   # SLURM batch script used to run the solver on Dardel (PDC/NAISS)
└── postProcessing/        # probe time series (H2, residuals) used to generate all reported figures

python_script/     # ceiling H2 vs. flow rate, turbulence/grid sensitivity, vertical profiles,
                    # probe/residual time-series plots
paraview_script/    # ParaView Python scripts and drivers for volume-fraction and velocity
                    # field snapshots (Figs. 7, 8, 10)
```

## Reproducing a case

Meshing is done locally; only the solver is run on HPC.

```bash
# 1. Mesh generation (local)
cd <case_dir>
bash Allclean && bash Allrun
# copies 0.orig -> 0, then runs surfaceFeatureExtract, blockMesh, snappyHexMesh,
# topoSet, createPatch, checkMesh, renumberMesh, potentialFoam

# 2. Solver run (HPC, SLURM)
sbatch sbatch_OF_dardel_monitor
# adjust the SLURM account (-A) and module paths for your own cluster/allocation

# 3. Post-processing
cd ../python_script
python3 check_probe_timeseries.py <case_number>
python3 ceiling_H2_vs_flow_rate_1m3_paired.py   # or _2m3_paired.py
```

`postProcessing/` in each case directory already contains the probe time series produced by the
original runs, so the plotting scripts above can be run immediately without re-solving.

## Turbulence model

RANS with the standard k–ε model (selected via the sensitivity study in Fig. 4); k–ω SST and
RNG k–ε were also evaluated (cases 29, 31).

## Experimental reference data

Experimental values used for validation are taken from Bernard-Michel, G., Houssin-Agbomson, D.
(2017), *Comparison of helium and hydrogen releases in 1 m³ and 2 m³ two vents enclosures*,
Int. J. Hydrogen Energy 42, 7542–7550, https://doi.org/10.1016/j.ijhydene.2016.05.217, and are
reproduced in the plotting scripts as reference arrays (not redistributed as raw experimental
data).

## Acknowledgements

This work was supported by the European Union's Horizon Europe research and innovation
programme through the NavHys project (Grant Agreement No. 101192425). Computations were enabled
by resources provided by the National Academic Infrastructure for Supercomputing in Sweden
(NAISS), partially funded by the Swedish Research Council through grant agreement no.
2022-06725. NAISS project 2026/3-176 is acknowledged.

## License

See [LICENSE](LICENSE) (MIT).
