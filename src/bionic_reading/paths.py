from __future__ import annotations

from pathlib import Path


def bionic_output_path(input_path: Path) -> Path:
    """Return the default output path: same location, stem with '-bionic' appended."""
    return input_path.with_name(f"{input_path.stem}-bionic{input_path.suffix}")
