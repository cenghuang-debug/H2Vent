# Zoomed U velocity snapshot for 2 m³ enclosure interior.
# Camera shows only the enclosure (±0.48 m in Y, 0–2.1 m in Z), excluding external domain.
# Vent side (y = -0.48 m) extended slightly to show vent openings.
# Each case auto-scales its own colorbar — intended for side-by-side nozzle comparison.
#
# Usage:
#   pvpython paraview_script_2m3_zoom_U_linux.py <case_name> [--debug]
#   e.g.:
#   pvpython paraview_script_2m3_zoom_U_linux.py 2m3_27mm_wall_H2_test_56 --debug
#   pvpython paraview_script_2m3_zoom_U_linux.py 2m3_4mm_wall_H2_test_72  --debug

import argparse, os, sys

# ── User settings ─────────────────────────────────────────────────────────────
CASE_NAME   = '2m3_27mm_wall_H2_test_56'
DEBUG       = False
IMG_WIDTH   = 2400
IMG_HEIGHT  = 5200   # portrait — enclosure is ~0.96 m wide × 2.1 m tall

# Camera bounds: enclosure interior + vent side extension (scale 0.001 → metres)
# Vents are on y = -0.48 m wall; extend to -0.62 m to show them.
ENC_Y_MIN   = -0.62
ENC_Y_MAX   =  0.48
ENC_Z_MIN   =  0.0
ENC_Z_MAX   =  2.1
MARGIN_TOP  =  0.05
MARGIN_BOT  =  0.15   # space for colorbar below enclosure
MARGIN_SIDE =  0.05

CB_TITLE_SIZE = 30
CB_LABEL_SIZE = 26
CB_THK        = 16
SLICE_X       = 0.001

GLYPH_SCALE  = 0.06
GLYPH_STRIDE = 16
VEL_CB_POS   = [0.10, 0.02]
VEL_CB_LEN   = 0.80
# ──────────────────────────────────────────────────────────────────────────────

parser = argparse.ArgumentParser()
parser.add_argument('case_name', nargs='?', default=CASE_NAME)
parser.add_argument('--debug',   action='store_true', default=DEBUG)
args, _ = parser.parse_known_args()

DEBUG = args.debug

BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
foam_file = os.path.join(BASE_PATH, args.case_name, 'open.foam')

print(f'Case  : {args.case_name}')
print(f'Debug : {DEBUG}')
print(f'File  : {foam_file}')

from paraview.simple import *
paraview.simple._DisableFirstRenderCameraReset()

openfoam = OpenFOAMReader(registrationName='open.foam', FileName=foam_file)
animationScene1 = GetAnimationScene()
animationScene1.UpdateAnimationUsingDataTimeSteps()

renderView1 = GetActiveViewOrCreate('RenderView')
renderView1.UseColorPaletteForBackground = 0
renderView1.Background = [1.0, 1.0, 1.0]
openfoamDisplay = Show(openfoam, renderView1, 'UnstructuredGridRepresentation')
renderView1.ResetCamera()
renderView1.Update()

pLUT = GetColorTransferFunction('p')
pLUT.ScalarRangeInitialized = 1.0
pPWF = GetOpacityTransferFunction('p')
pPWF.ScalarRangeInitialized = 1

# Slice at symmetry plane
slice_U = Slice(registrationName='SliceU', Input=openfoam)
slice_U.SliceType        = 'Plane'
slice_U.SliceType.Origin = [SLICE_X, 0.0, 1.0]
slice_U.SliceType.Normal = [1.0, 0.0, 0.0]
slice_U.Triangulatetheslice = 0

slice_UDisplay = Show(slice_U, renderView1, 'GeometryRepresentation')
ColorBy(slice_UDisplay, ('POINTS', 'U'))
uLUT = GetColorTransferFunction('U')
uLUT.VectorMode = 'Magnitude'
uPWF = GetOpacityTransferFunction('U')
slice_UDisplay.RescaleTransferFunctionToDataRange(True, False)
uLUT.ApplyPreset('X Ray', True)
# Flat (unlit) shading — otherwise the default headlight darkens/tints the
# U=0 (pure white) regions into a warm gray instead of matching the white
# renderView background.
slice_UDisplay.Ambient = 1.0
slice_UDisplay.Diffuse = 0.0

Hide(openfoam, renderView1)

glyph1 = Glyph(registrationName='VelocityGlyph', Input=slice_U)
glyph1.GlyphType        = 'Arrow'
glyph1.OrientationArray = ['POINTS', 'U']
glyph1.ScaleArray       = ['POINTS', 'No scale array']
glyph1.ScaleFactor = GLYPH_SCALE
glyph1.GlyphMode   = 'Every Nth Point'
glyph1.Stride      = GLYPH_STRIDE

glyph1Display = Show(glyph1, renderView1, 'GeometryRepresentation')
ColorBy(glyph1Display, ('POINTS', 'U'))

# Always set up the colorbar widget; visibility toggled per save
slice_UDisplay.SetScalarBarVisibility(renderView1, False)
uLUTColorBar = GetScalarBar(uLUT, renderView1)
uLUTColorBar.Title          = '$\\vert U\\vert$ (m/s)'
uLUTColorBar.ComponentTitle = ''
uLUTColorBar.TitleColor     = [0.0, 0.0, 0.0]
uLUTColorBar.LabelColor     = [0.0, 0.0, 0.0]
uLUTColorBar.TitleFontSize  = CB_TITLE_SIZE
uLUTColorBar.LabelFontSize  = CB_LABEL_SIZE
uLUTColorBar.Orientation        = 'Horizontal'
uLUTColorBar.WindowLocation     = 'Any Location'
uLUTColorBar.Position           = VEL_CB_POS
uLUTColorBar.ScalarBarLength    = VEL_CB_LEN
uLUTColorBar.ScalarBarThickness = CB_THK

renderView1.OrientationAxesVisibility = 0
layout1 = GetLayout()
layout1.SetSize(1000, 1000)


def setup_camera():
    y_range  = ENC_Y_MAX - ENC_Y_MIN
    z_range  = ENC_Z_MAX - ENC_Z_MIN
    y_center = (ENC_Y_MIN + ENC_Y_MAX) / 2.0
    z_center = (ENC_Z_MIN + ENC_Z_MAX) / 2.0 + (z_range / 2.0) * (MARGIN_TOP - MARGIN_BOT)
    aspect   = IMG_WIDTH / IMG_HEIGHT
    ps_z = (z_range / 2.0) * (1 + MARGIN_TOP + MARGIN_BOT)
    ps_y = (y_range / 2.0) * (1 + 2 * MARGIN_SIDE) / aspect
    ps   = max(ps_z, ps_y)
    bounds = openfoam.GetDataInformation().GetBounds()
    cam_x  = bounds[0] - 1.0
    renderView1.CameraParallelProjection = 1
    renderView1.CameraPosition   = [cam_x,     y_center, z_center]
    renderView1.CameraFocalPoint = [bounds[0], y_center, z_center]
    renderView1.CameraViewUp     = [0.0, 0.0, 1.0]
    renderView1.CameraParallelScale = ps
    print(f'Camera: y_center={y_center:.3f}, z_center={z_center:.3f}, PS={ps:.3f}')

setup_camera()

OUTPUT_DIR = 'U_zoom'

def save_all_timesteps():
    output_dir = os.path.join(BASE_PATH, args.case_name, 'U', OUTPUT_DIR)
    os.makedirs(output_dir, exist_ok=True)
    times = list(openfoam.TimestepValues) or [animationScene1.AnimationTime]
    if DEBUG:
        times = [times[-1]]
        print(f'DEBUG: saving 1 screenshot (last t={times[0]:.3f}s)')
    else:
        print(f'Saving {len(times)} screenshot(s) to: {output_dir}')
    for t in times:
        animationScene1.AnimationTime = t
        renderView1.Update()
        Render()
        # Save without colorbar
        slice_UDisplay.SetScalarBarVisibility(renderView1, False)
        Render()
        fname = os.path.join(output_dir, f'U_zoom_t{t:010.3f}s.png')
        SaveScreenshot(fname, renderView1,
                       ImageResolution=[IMG_WIDTH, IMG_HEIGHT],
                       TransparentBackground=0)
        print(f'  Saved (no CB) t={t:.3f}s -> {os.path.basename(fname)}')
        # Save with colorbar
        slice_UDisplay.SetScalarBarVisibility(renderView1, True)
        Render()
        fname_cb = os.path.join(output_dir, f'U_zoom_cb_t{t:010.3f}s.png')
        SaveScreenshot(fname_cb, renderView1,
                       ImageResolution=[IMG_WIDTH, IMG_HEIGHT],
                       TransparentBackground=0)
        print(f'  Saved (with CB) t={t:.3f}s -> {os.path.basename(fname_cb)}')

save_all_timesteps()
