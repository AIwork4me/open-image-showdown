"""CI gate over the full gallery — same engine as tools/validate_gallery.py."""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))

import validate_gallery  # noqa: E402


def test_gallery_integrity():
    fails = validate_gallery.validate(REPO)
    assert not fails, "gallery integrity failures:\n  - " + "\n  - ".join(fails)
