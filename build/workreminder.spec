# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
import sys


project_root = Path(SPECPATH).parent
icon_path = project_root / "picuture_256x256.ico"

a = Analysis(
    [str(project_root / "main.py")],
    pathex=[str(project_root)],
    binaries=[],
    datas=[(str(icon_path), ".")] if icon_path.exists() else [],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[str(project_root / "build" / "runtime_hook.py")],
    excludes=[],
    noarchive=False,
    optimize=0,
)
# The build host may expose Poppler's versioned ICU DLLs through PATH.  They
# are unrelated to this application and conflict with QtCore's unversioned
# ICU imports (for example, ucnv_open).  Windows 10/11 provides the matching
# system ICU DLL, so do not bundle the incompatible copies.
conflicting_icu_names = {"icuuc.dll", "icudt78.dll"}
a.binaries = [
    entry
    for entry in a.binaries
    if Path(entry[0]).name.lower() not in conflicting_icu_names
]
# ctypes and Python's decimal extension use these Conda runtime libraries.
# They are available at runtime in the development environment but are not
# automatically discovered by PyInstaller from this Conda installation.
conda_bin = Path(sys.base_prefix) / "Library" / "bin"
for runtime_name in ("ffi.dll", "libmpdec-4.dll"):
    runtime_path = conda_bin / runtime_name
    if runtime_path.exists():
        a.binaries.append((runtime_name, str(runtime_path), "BINARY"))
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="workreminder_v1",
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
    icon=str(icon_path) if icon_path.exists() else None,
)
