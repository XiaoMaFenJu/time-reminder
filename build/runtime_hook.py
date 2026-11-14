"""Make PySide6's bundled native libraries discoverable in one-file builds."""

from __future__ import annotations

import os
import sys


if getattr(sys, "frozen", False):
    bundle_root = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    for relative_path in (".", "PySide6", "shiboken6"):
        native_dir = os.path.join(bundle_root, relative_path)
        if os.path.isdir(native_dir):
            if hasattr(os, "add_dll_directory"):
                os.add_dll_directory(native_dir)
            os.environ["PATH"] = native_dir + os.pathsep + os.environ.get("PATH", "")
