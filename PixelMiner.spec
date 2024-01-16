# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['PixelMiner.py'],
    pathex=[],
    binaries=[],
    datas=[('scripts', 'scripts'), ('assets', 'assets'), ('Version_Mappings', 'Version_Mappings')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='PixelMiner',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets\\PixelMiner.ico'],
)
