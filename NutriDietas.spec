# -*- mode: python ; coding: utf-8 -*-
# Build reproducible de NutriDietas con PyInstaller.
#
#   pip install pyinstaller
#   pyinstaller NutriDietas.spec
#
# Genera dist/NutriDietas/NutriDietas.exe (modo carpeta) con el icono y con
# datos/, recursos/ y plantillas/ al lado del .exe para que el nutriologo
# pueda editarlos (catalogo, logo, plantillas).

block_cipher = None

a = Analysis(
    ['gui.pyw'],
    pathex=[],
    binaries=[],
    datas=[
        ('datos', 'datos'),
        ('recursos', 'recursos'),
        ('plantillas', 'plantillas'),
    ],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
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
    upx=True,
    console=False,               # app de ventana, sin consola
    icon='recursos/icono.ico',   # icono del .exe
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='NutriDietas',
)
