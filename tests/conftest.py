from __future__ import annotations

import os
import sys


def pytest_configure() -> None:
    """
    Ensure the project's `src/` directory is importable in tests, matching `run.py`.
    """
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src_dir = os.path.join(repo_root, "src")
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
