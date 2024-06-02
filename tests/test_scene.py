from pathlib import Path
from thps_formats.graphics.scene import Scene


# -------------------------------------------------------------------------------------------------
# THUG2_LEVELS_PATH = Path('D:/Games/THUG2/Game/Data/Levels')
THUG2_LEVELS_PATH = Path('E:/Backup/THPS_ISO/THUG2_XBX/data/extracted/levels')
THUG2_MODELS_PATH = Path('E:/Backup/THPS_ISO/THUG2_XBX/data/extracted/models')


# # -------------------------------------------------------------------------------------------------
# def test_scene():
#     scene = Scene.from_files([
#         # './tests/data/ba.q',
#         './tests/data/ba.scn.xbx',
#         # './tests/data/ba.col.xbx',
#         # './tests/data/ba.tex.xbx',
#     ])


# -------------------------------------------------------------------------------------------------
def test_lod_levels():
    for filename in THUG2_LEVELS_PATH.rglob('*.scn.xbx'):
        if filename.is_file():
            print('--- loading scene', filename)
            Scene.from_file(filename)

# # -------------------------------------------------------------------------------------------------
# def test_models():
#     for filename in THUG2_MODELS_PATH.rglob('*.mdl.xbx'):
#         if filename.is_file():
#             print('--- loading model', filename)
#             Scene.from_file(filename)
