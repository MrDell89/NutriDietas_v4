# -*- mode: python ; coding: utf-8 -*-
# Build reproducible de NutriDietas con PyInstaller.
#
#   pip install pyinstaller
#   pyinstaller NutriDietas.spec --clean --noconfirm
#
# Genera dist/NutriDietas/NutriDietas.exe (modo carpeta). IMPORTANTE: la app
# se ejecuta desde dist/, NO desde build/ (build es intermedia).
#
# Las dependencias de terceros (python-docx, reportlab, Pillow) se incluyen
# completas con collect_all para evitar modulos o datos faltantes.

from PyInstaller.utils.hooks import collect_all

datas = [
    ('datos', 'datos'),
    ('recursos', 'recursos'),
    ('plantillas', 'plantillas'),
]
binaries = []
hiddenimports = []

for _paquete in ('docx', 'reportlab', 'PIL'):
    _d, _b, _h = collect_all(_paquete)
    datas += _d
    binaries += _b
    hiddenimports += _h

block_cipher = None

a = Analysis(
    ['gui.pyw'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=['pygame'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='NutriDietas',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,               # app de ventana, sin consola
    icon='recursos/icono.ico',   # icono del .exe
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='NutriDietas',
)
