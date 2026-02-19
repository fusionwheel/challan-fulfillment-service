# -*- mode: python ; coding: utf-8 -*-
import os
import playwright_stealth

stealth_path = os.path.dirname(playwright_stealth.__file__)

# --- Analysis for BOTH scripts ---
a = Analysis(
    ['main.py'],
    pathex=["."],
    binaries=[],
    datas=[('.svc', '.svc'), ('.env', '.'), ('run.sh', '.'), (os.path.join(stealth_path, 'js'), 'playwright_stealth/js')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['workflow'], 
    noarchive=False,
)

# --- Add a second Analysis for the worker ---
a_worker = Analysis(
    ['sms_worker.py'],
    pathex=["."],
    binaries=[],
    datas=[], # main.py analysis already handles global datas
    hiddenimports=['uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on'],
    excludes=['workflow'],
    noarchive=False,
)

pyz = PYZ(a.pure)
pyz_worker = PYZ(a_worker.pure)

# --- EXE for main service ---
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='fulfillment_svc',
    debug=False,
    upx=True,
    console=True,
)

# --- EXE for sms_worker ---
exe_worker = EXE(
    pyz_worker,
    a_worker.scripts,
    [],
    exclude_binaries=True,
    name='sms_worker', # This creates the file subprocess is looking for
    debug=False,
    upx=True,
    console=True,
)

# --- COLLECT everything into one folder ---
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    exe_worker,        # Add worker exe
    a_worker.binaries, # Add worker binaries
    a_worker.datas,    # Add worker datas
    strip=False,
    upx=True,
    upx_exclude=[],
    name='fulfillment_svc',
)