"""File counting utilities for repositories."""

from pathlib import Path
import os

EXCLUDED_DIRS = {".git", "node_modules", "venv", ".venv", "__pycache__"}


def _is_hidden(name: str) -> bool:
    """Return True if a path component should be considered hidden."""
    return name.startswith(".")


def count_files(root: Path) -> int:
    """Count non-hidden files under root while skipping common vendor/venv dirs."""
    total = 0
    for _dirpath, _dirnames, filenames in _walk_filtered(root):
        total += sum(1 for name in filenames if not _is_hidden(name))
    return total


def write_file_count_file(root: Path, count: int) -> Path:
    """Write the count to `file_count` at root and return the path."""
    target = root / "file_count"
    target.write_text(str(count), encoding="utf-8")
    return target


def _walk_filtered(root: Path):
    """Yield walk results while pruning excluded/hidden directories."""
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            d
            for d in dirnames
            if d not in EXCLUDED_DIRS and not _is_hidden(d)
        ]
        yield dirpath, dirnames, filenames

