# -*- mode: python ; coding: utf-8 -*-
"""packaging/kast.spec — PyInstaller bundle specification for Kast Studio Windows Edition."""

import os
import sys

try:
    spec_dir = SPECPATH
except NameError:
    spec_dir = os.path.abspath(os.path.dirname(__file__)) if "__file__" in globals() else os.getcwd()

SPECPATH = spec_dir
ROOT_DIR = os.path.abspath(os.path.join(SPECPATH, ".."))

block_cipher = None

datas = [
    (os.path.join(ROOT_DIR, "docs"), "docs"),
    (os.path.join(SPECPATH, "assets"), os.path.join("packaging", "assets")),
]

example_dir = os.path.join(ROOT_DIR, "example")
if os.path.isdir(example_dir):
    datas.append((example_dir, "example"))

hiddenimports = [
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
    "docx",
    "pdfplumber",
    "pypdf",
    "PIL",
    "src.version",
    "src.updater",
    "src.updater_gui",
]

excludes = [
    "tkinter",
    "matplotlib",
    "scipy",
    "notebook",
    "IPython",
]

# Windows 10/11 system-level Unicode libraries for Qt6 / Wine compatibility
binaries = []
if sys.platform == "win32":
    system32 = os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32")
    for dll in ["icuuc.dll", "icuin.dll", "icudt.dll"]:
        dll_path = os.path.join(system32, dll)
        if os.path.isfile(dll_path):
            binaries.append((dll_path, "."))

a = Analysis(
    [os.path.join(SPECPATH, "run_gui.py")],
    pathex=[ROOT_DIR],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
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
    name="KastStudio",
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
    icon=os.path.join(SPECPATH, "assets", "kast.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="KastStudio",
)
