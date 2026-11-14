# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

# Reuse the maintained build configuration while giving this release its own name.
spec_path = Path(SPECPATH) / "workreminder.spec"
source = spec_path.read_text(encoding="utf-8")
exec(compile(source.replace('name="workreminder_v1"', 'name="workreminder_v0_2"'), str(spec_path), "exec"))
