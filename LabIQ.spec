# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['launcher.py'],
    pathex=[],
    binaries=[],
    datas=[('static', 'static'), ('data', 'data'), ('main.py', '.'), ('models.py', '.'), ('auth.py', '.'), ('database.py', '.')],
    hiddenimports=['fastapi', 'fastapi.staticfiles', 'fastapi.templating', 'fastapi.responses', 'fastapi.middleware', 'fastapi.middleware.cors', 'uvicorn', 'uvicorn.logging', 'uvicorn.loops', 'uvicorn.loops.auto', 'uvicorn.protocols', 'uvicorn.protocols.http', 'uvicorn.protocols.http.auto', 'uvicorn.protocols.websockets', 'uvicorn.protocols.websockets.auto', 'uvicorn.lifespan', 'uvicorn.lifespan.on', 'sqlalchemy', 'sqlalchemy.ext.declarative', 'sqlalchemy.orm', 'sqlalchemy.dialects.sqlite', 'passlib', 'passlib.handlers.sha2_crypt', 'jose', 'jose.jwt', 'jose.exceptions', 'jose.constants', 'jose.backends', 'multipart', 'pandas', 'openpyxl', 'sklearn', 'anthropic', 'aiofiles', 'dotenv'],
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
    a.binaries,
    a.datas,
    [],
    name='LabIQ',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['labiq.ico'],
)
