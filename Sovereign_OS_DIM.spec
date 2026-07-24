# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('frontend', 'frontend'), ('backend/ml/models', 'backend/ml/models')]
binaries = []
hiddenimports = ['clr', 'clr_loader', 'clr_loader.ffi', 'clr_loader.ffi.coreclr', 'clr_loader.ffi.mono', 'clr_loader.ffi.netfx', 'pythonnet', 'cffi', 'pycparser', 'backend.orgchart.structure', 'backend.interfaces.api', 'backend.interfaces._sentinel', 'backend.pmsi.data_processor', 'backend.ml', 'backend.ml.predict', 'backend.ml.synthetic', 'openpyxl', 'xgboost', 'lightgbm', 'sklearn.ensemble._forest', 'sklearn.tree._utils', 'numpy']
tmp_ret = collect_all('webview')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('clr_loader')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('pythonnet')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Sovereign_OS_DIM',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['frontend\\favicon.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Sovereign_OS_DIM',
)
