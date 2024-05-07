# -*- mode: python ; coding: utf-8 -*-

tools = [
    {'name': 'qcompy', 'scripts': ['qcompy/qcompy.py'], 'icon': 'qcompy/qcompy.ico'},
    {'name': 'prepack', 'scripts': ['prepack/prepack.py'], 'icon': 'prepack/prepack.ico'},
    {'name': 'fontgen', 'scripts': ['fontgen/fontgen.py'], 'hiddenimports': ['PIL', 'PIL._imaging', 'PIL.Image'], 'icon': 'fontgen/fontgen.ico'},
    {'name': 'asscopy', 'scripts': ['asscopy/asscopy.py'], 'icon': 'asscopy/asscopy.ico'},
]

analysis = {t['name']: Analysis(
    scripts=t.get('scripts', None),
    pathex=['../'],
    binaries=t.get('binaries', []),
    datas=t.get('datas', []),
    hiddenimports=t.get('hiddenimports', []),
    hookspath=t.get('hookspath', []),
    hooksconfig=t.get('hooksconfig', {}),
    runtime_hooks=t.get('runtime_hooks', []),
    excludes=t.get('excludes', []),
    noarchive=t.get('noarchive', False),
) for t in tools}

executables = {t['name']: EXE(
    PYZ(analysis[t['name']].pure),
    analysis[t['name']].scripts,
    [],
    exclude_binaries=t.get('exclude_binaries', True),
    name=t['name'],
    debug=t.get('debug', False),
    bootloader_ignore_signals=t.get('bootloader_ignore_signals', False),
    strip=t.get('strip', False),
    upx=t.get('upx', True),
    console=t.get('console', True),
    disable_windowed_traceback=t.get('disable_windowed_traceback', False),
    argv_emulation=t.get('argv_emulation', False),
    target_arch=t.get('target_arch', None),
    codesign_identity=t.get('codesign_identity', None),
    entitlements_file=t.get('entitlements_file', None),
    icon=[t.get('icon')],
) for t in tools}

collectargs = []
for key in executables.keys():
    collectargs.extend([
        executables[key],
        analysis[key].binaries,
        analysis[key].zipfiles,
        analysis[key].datas,
    ])

coll = COLLECT(
    *collectargs,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='tools',
)
