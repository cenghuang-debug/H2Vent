# Linux-adapted version of paraview_script_1m3_external_H2_U.py
# Runs headless via pvpython; accepts case_name and --mode on the command line.
#
# Usage:
#   pvpython paraview_script_1m3_linux.py <case_name> [--mode H2_vol_con|U] [--debug]
#   e.g.:
#   pvpython paraview_script_1m3_linux.py 1m3_27mm_wall_H2_test_68 --mode H2_vol_con

import argparse, os, sys

# ── User settings ─────────────────────────────────────────────────────────────
CASE_NAME   = '1m3_27mm_wall_H2_test_68'
DEBUG       = False
IMG_WIDTH   = 3000
IMG_HEIGHT  = 2000

ENC_Y_MIN   = -1.5
ENC_Y_MAX   =  1.5
ENC_Z_MIN   =  0.0
ENC_Z_MAX   =  2.0       # full domain height — keeps camera height-limited for correct margins
MARGIN_TOP  =  0.08
MARGIN_BOT  =  0.22
MARGIN_SIDE =  0.10

CB_POS        = [0.10, 0.01]
CB_LEN        = 0.80
CB_THK        = 16
# Colorbar title/label sizes DO scale with SaveScreenshot magnification in
# ParaView 5.10, so keep them at the original viewport-pt values.
CB_TITLE_SIZE = 18
CB_LABEL_SIZE = 16

TEXT_SIZE   = 71    # scaled to match case 55 (Windows/PV5.12): 50 * (55px/39px) ≈ 71
SLICE_X     =  0.001

MODE        = 'H2_vol_con'    # default; overridden by --mode
VEL_MAX     = None
GLYPH_SCALE = 0.1
GLYPH_STRIDE= 4
SHOW_VEL_CB = True
VEL_CB_POS  = [0.10, 0.01]
VEL_CB_LEN  = 0.80
# ──────────────────────────────────────────────────────────────────────────────

parser = argparse.ArgumentParser()
parser.add_argument('case_name', nargs='?', default=CASE_NAME)
parser.add_argument('--mode',   default=MODE, choices=['H2_vol_con', 'U'],
                    help='Visualization mode: H2_vol_con or U')
parser.add_argument('--stride', type=int, default=GLYPH_STRIDE)
parser.add_argument('--debug',  action='store_true', default=DEBUG)
args, _ = parser.parse_known_args()

MODE         = args.mode
GLYPH_STRIDE = args.stride
DEBUG        = args.debug

BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
foam_file = os.path.join(BASE_PATH, args.case_name, 'open.foam')

print(f'Case  : {args.case_name}')
print(f'Mode  : {MODE}')
print(f'Debug : {DEBUG}')
print(f'File  : {foam_file}')

from paraview.simple import *
paraview.simple._DisableFirstRenderCameraReset()

openfoam = OpenFOAMReader(registrationName='open.foam', FileName=foam_file)
animationScene1 = GetAnimationScene()
animationScene1.UpdateAnimationUsingDataTimeSteps()

renderView1 = GetActiveViewOrCreate('RenderView')
openfoamDisplay = Show(openfoam, renderView1, 'UnstructuredGridRepresentation')
openfoamDisplay.Representation = 'Surface'
renderView1.ResetCamera()
materialLibrary1 = GetMaterialLibrary()
openfoamDisplay.SetScalarBarVisibility(renderView1, True)
renderView1.Update()

pLUT  = GetColorTransferFunction('p')
pLUT.ScalarRangeInitialized = 1.0
pPWF = GetOpacityTransferFunction('p')
pPWF.ScalarRangeInitialized = 1

renderView1.ResetCamera()

ColorBy(openfoamDisplay, ('POINTS', 'H2'))
HideScalarBarIfNotNeeded(pLUT, renderView1)
openfoamDisplay.RescaleTransferFunctionToDataRange(True, False)
openfoamDisplay.SetScalarBarVisibility(renderView1, True)

h2LUT  = GetColorTransferFunction('H2')
h2LUT.ScalarRangeInitialized = 1.0
h2PWF = GetOpacityTransferFunction('H2')
h2PWF.ScalarRangeInitialized = 1

openfoam = FindSource('open.foam')

# Calculator: Y_H2 (mass fraction) → X_H2 (volume fraction)
# X = (Y/M_H2) / (Y/M_H2 + (1-Y)/M_air)  with M_H2=2, M_air=29 g/mol
calculator1 = Calculator(registrationName='Calculator1', Input=openfoam)
calculator1.ResultArrayName = 'X_H2'
calculator1.Function = 'H2/2*(1/(H2/2+(1-H2)/29))'

renderView1 = GetActiveViewOrCreate('RenderView')
renderView1.UseColorPaletteForBackground = 0
materialLibrary1 = GetMaterialLibrary()
renderView1.Background = [1.0, 1.0, 1.0]

x_H2LUT  = GetColorTransferFunction('X_H2')
x_H2LUT.ScalarRangeInitialized = 1.0
# White -> yellow -> red ramp (0 -> 0.5 -> 1.0, normalised control points;
# rescaled to [0, 0.04] below). High end reads as "elevated concentration"
# since 0.04 approaches the H2 flammability limit (~4 vol%).
x_H2LUT.RGBPoints = [
    0.0, 1.0, 1.0, 1.0,
    0.5, 1.0, 1.0, 0.0,
    1.0, 1.0, 0.0, 0.0,
]
x_H2LUT.ColorSpace = 'RGB'
x_H2PWF = GetOpacityTransferFunction('X_H2')
x_H2PWF.ScalarRangeInitialized = 1

calculator1 = GetActiveSource()
calculator1Display = GetDisplayProperties(calculator1, view=renderView1)
ColorBy(calculator1Display, ('POINTS', 'X_H2'))

openfoamDisplay.SetScalarBarVisibility(renderView1, False)
Hide(openfoam, renderView1)
HideScalarBarIfNotNeeded(x_H2LUT, renderView1)
calculator1Display.RescaleTransferFunctionToDataRange(True, False)
calculator1Display.SetScalarBarVisibility(renderView1, True)

x_H2LUTColorBar = GetScalarBar(x_H2LUT, renderView1)
x_H2LUTColorBar.Title           = '$X_{H_2}$'
x_H2LUTColorBar.ComponentTitle  = ''
x_H2LUTColorBar.TitleColor      = [0.0, 0.0, 0.0]
x_H2LUTColorBar.LabelColor      = [0.0, 0.0, 0.0]
x_H2LUTColorBar.TitleFontSize   = CB_TITLE_SIZE
x_H2LUTColorBar.LabelFontSize   = CB_LABEL_SIZE
x_H2LUTColorBar.Orientation        = 'Horizontal'
x_H2LUTColorBar.WindowLocation     = 'Any Location'
x_H2LUTColorBar.Position           = CB_POS
x_H2LUTColorBar.ScalarBarLength    = CB_LEN
x_H2LUTColorBar.ScalarBarThickness = CB_THK

x_H2LUT.RescaleTransferFunction(0.0, 0.04)
x_H2PWF.RescaleTransferFunction(0.0, 0.04)

# Cell Data to Point Data — smooths coarse-mesh banding near boundaries
cellDataToPointData1 = CellDatatoPointData(
    registrationName='CellDatatoPointData1', Input=calculator1)

Hide(calculator1, renderView1)
Hide(cellDataToPointData1, renderView1)

slice1 = Slice(registrationName='Slice1', Input=cellDataToPointData1)
slice1.SliceType = 'Plane'
slice1.SliceType.Origin = [SLICE_X, 0.0, 1.0]
slice1.SliceType.Normal = [1.0, 0.0, 0.0]
slice1.Triangulatetheslice = 0

slice1Display = Show(slice1, renderView1, 'GeometryRepresentation')
ColorBy(slice1Display, ('POINTS', 'X_H2'))
slice1Display.SetScalarBarVisibility(renderView1, True)
# Flat (unlit) shading — otherwise the default headlight darkens/tints the
# X_H2=0 (pure white) regions into a warm gray instead of matching the
# white renderView background.
slice1Display.Ambient = 1.0
slice1Display.Diffuse = 0.0

x_H2LUT.RescaleTransferFunction(0.0, 0.04)
x_H2PWF.RescaleTransferFunction(0.0, 0.04)

# Room outline: slice the actual enclosure shell STL (used by snappyHexMesh
# to build the walls) through the same cut-plane, so the outline traces the
# true wall geometry rather than a guessed bounding box.
room_stl = os.path.join(BASE_PATH, args.case_name, 'constant', 'triSurface', 'box_shell_m.stl')
if os.path.exists(room_stl):
    roomShell = STLReader(registrationName='RoomShell', FileNames=[room_stl])
    roomSlice = Slice(registrationName='RoomOutline', Input=roomShell)
    roomSlice.SliceType = 'Plane'
    roomSlice.SliceType.Origin = [SLICE_X, 0.0, 1.0]
    roomSlice.SliceType.Normal = [1.0, 0.0, 0.0]
    roomSlice.Triangulatetheslice = 0

    roomOutlineDisplay = Show(roomSlice, renderView1, 'GeometryRepresentation')
    ColorBy(roomOutlineDisplay, None)  # solid color, not colored by (absent) X_H2 array
    roomOutlineDisplay.Representation = 'Wireframe'
    roomOutlineDisplay.AmbientColor = [0.0, 0.0, 0.0]
    roomOutlineDisplay.DiffuseColor = [0.0, 0.0, 0.0]
    roomOutlineDisplay.LineWidth = 3.0
    roomOutlineDisplay.Ambient = 1.0
    roomOutlineDisplay.Diffuse = 0.0
    roomOutlineDisplay.SetScalarBarVisibility(renderView1, False)
else:
    print(f'[WARNING] room shell STL not found, skipping outline: {room_stl}')

# HideInteractiveWidgets not available in ParaView 5.10


def setup_velocity():
    if MODE != 'U':
        return
    Hide(slice1, renderView1)
    slice1Display.SetScalarBarVisibility(renderView1, False)
    HideScalarBarIfNotNeeded(x_H2LUT, renderView1)

    slice_U = Slice(registrationName='SliceU', Input=openfoam)
    slice_U.SliceType        = 'Plane'
    slice_U.SliceType.Origin = [SLICE_X, 0.0, 1.0]
    slice_U.SliceType.Normal = [1.0, 0.0, 0.0]
    slice_U.Triangulatetheslice = 0
    # HideInteractiveWidgets not available in ParaView 5.10

    slice_UDisplay = Show(slice_U, renderView1, 'GeometryRepresentation')
    ColorBy(slice_UDisplay, ('POINTS', 'U'))
    uLUT = GetColorTransferFunction('U')
    uLUT.VectorMode = 'Magnitude'
    uPWF = GetOpacityTransferFunction('U')
    if VEL_MAX is not None:
        uLUT.RescaleTransferFunction(0.0, VEL_MAX)
        uPWF.RescaleTransferFunction(0.0, VEL_MAX)
    else:
        slice_UDisplay.RescaleTransferFunctionToDataRange(True, False)
    uLUT.ApplyPreset('X Ray', True)

    glyph1 = Glyph(registrationName='VelocityGlyph', Input=slice_U)
    glyph1.GlyphType        = 'Arrow'
    glyph1.OrientationArray = ['POINTS', 'U']
    glyph1.ScaleArray       = ['POINTS', 'No scale array']
    glyph1.ScaleFactor      = GLYPH_SCALE
    glyph1.GlyphMode        = 'Every Nth Point'
    glyph1.Stride           = GLYPH_STRIDE

    glyph1Display = Show(glyph1, renderView1, 'GeometryRepresentation')
    ColorBy(glyph1Display, ('POINTS', 'U'))

    if SHOW_VEL_CB:
        slice_UDisplay.SetScalarBarVisibility(renderView1, True)
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
    else:
        slice_UDisplay.SetScalarBarVisibility(renderView1, False)

setup_velocity()

renderView1.OrientationAxesVisibility = 0

layout1 = GetLayout()
layout1.SetSize(1069, 829)


def setup_camera():
    y_half   = (ENC_Y_MAX - ENC_Y_MIN) / 2.0
    z_half   = (ENC_Z_MAX - ENC_Z_MIN) / 2.0
    y_center = (ENC_Y_MIN + ENC_Y_MAX) / 2.0
    z_center = (ENC_Z_MIN + ENC_Z_MAX) / 2.0 + z_half * (MARGIN_TOP - MARGIN_BOT)
    aspect   = IMG_WIDTH / IMG_HEIGHT
    ps_z = z_half * (1 + MARGIN_TOP + MARGIN_BOT)
    ps_y = y_half * (1 + 2 * MARGIN_SIDE) / aspect
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

timeText = Text(registrationName='TimeAnnotation')
timeText.Text = 't = 0 s'
timeTextDisplay = Show(timeText, renderView1, 'TextSourceRepresentation')
timeTextDisplay.Position      = [0.5, 0.92]
timeTextDisplay.FontSize      = TEXT_SIZE
timeTextDisplay.Color         = [0.0, 0.0, 0.0]
timeTextDisplay.Bold          = 0
timeTextDisplay.Justification = 'Center'


def save_all_timesteps():
    output_dir = os.path.join(BASE_PATH, args.case_name, MODE)
    os.makedirs(output_dir, exist_ok=True)
    times = list(openfoam.TimestepValues) or [animationScene1.AnimationTime]
    if DEBUG:
        times = [times[-1]]
        print(f'DEBUG: saving 1 screenshot (last t={times[0]:.3f}s)')
    else:
        print(f'Saving {len(times)} screenshot(s) to: {output_dir}')
    for t in times:
        animationScene1.AnimationTime = t
        timeText.Text = f't = {t:.1f} s'
        renderView1.Update()
        Render()
        fname = os.path.join(output_dir, f'{MODE}_t{t:010.3f}s.png')
        SaveScreenshot(fname, renderView1,
                       ImageResolution=[IMG_WIDTH, IMG_HEIGHT],
                       TransparentBackground=0)
        print(f'  Saved t={t:.3f}s -> {os.path.basename(fname)}')

save_all_timesteps()
