# -*- mode: python ; coding: utf-8 -*-

# Analysis object (defines what files/modules to analyze)
a = Analysis(
    ['src\\app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src/shaders', 'src/shaders'),  # Preserve full directory structure
        ('config.yml', '.'),  # Place config.yml directly in the bundle root
    ],
    hiddenimports=['tzdata'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

# PYZ object (handles Python bytecode)
pyz = PYZ(a.pure)

# EXE object (creates the executable)
# In onefile mode, EXE directly takes a.binaries, a.datas, etc.
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas, # Important: a.datas is passed directly to EXE
    [],
    name='HexaMapper',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False, # Or False for a windowed (GUI) application
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# **Important:** No COLLECT object for onefile mode!
