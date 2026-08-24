#!/bin/bash
# Run paraview_script_1m3_linux.py for cases 68-71, both H2 and U modes.
# Each case × mode is run sequentially to avoid memory issues.
#
# Usage:
#   bash run_paraview_cases68_71.sh
#   bash run_paraview_cases68_71.sh --debug    # last time step only

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PV_SCRIPT="${SCRIPT_DIR}/paraview_script_1m3_linux.py"

DEBUG_FLAG=""
if [[ "$1" == "--debug" ]]; then
    DEBUG_FLAG="--debug"
    echo "DEBUG mode: only last time step per case/mode"
fi

CASES=(68 69 70 71)
MODES=(H2_vol_con U)

for CASE in "${CASES[@]}"; do
    CASE_NAME="1m3_27mm_wall_H2_test_${CASE}"
    for MODE in "${MODES[@]}"; do
        echo "========================================"
        echo "Case: ${CASE_NAME}   Mode: ${MODE}"
        echo "========================================"
        PYTHONPATH=/usr/lib/python3/dist-packages \
        LIBGL_ALWAYS_SOFTWARE=1 MESA_GL_VERSION_OVERRIDE=4.5 \
        pvpython "${PV_SCRIPT}" "${CASE_NAME}" --mode "${MODE}" ${DEBUG_FLAG}
        if [[ $? -ne 0 ]]; then
            echo "[ERROR] pvpython failed for ${CASE_NAME} mode=${MODE}"
        else
            echo "[OK] Done: ${CASE_NAME} mode=${MODE}"
        fi
        echo ""
    done
done

echo "All done."
