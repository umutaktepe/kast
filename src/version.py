import os
import re
import subprocess
import sys
from typing import Tuple

__static_version__ = "2.1.4"


def get_version() -> str:
    """Return the application version string.

    In frozen/standalone mode (PyInstaller), returns the static version injected during build.
    In development mode (source checkout), dynamically resolves the latest git tag if available.
    """
    if getattr(sys, "frozen", False):
        return __static_version__

    try:
        repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        tag = subprocess.check_output(
            ["git", "describe", "--tags", "--abbrev=0"],
            cwd=repo_dir,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=1.5,
        ).strip()
        if tag:
            clean = tag.lstrip("vV")
            if re.match(r"^\d+(\.\d+)*", clean):
                return clean
    except Exception:
        pass

    return __static_version__


__version__ = get_version()


def parse_version(version_str: str) -> Tuple[int, ...]:
    """Parse a semantic version string (e.g. 'v2.1.1' or '2.1.1') into an integer tuple.

    Non-digit suffixes or prefixes are safely stripped.
    """
    clean_str = version_str.strip().lstrip("vV")
    # Sayısal blokları topla
    parts = re.findall(r"\d+", clean_str)
    if not parts:
        return (0,)
    return tuple(int(p) for p in parts)


def is_newer_version(remote_version: str, current_version: str = __version__) -> bool:
    """Return True if remote_version is strictly newer than current_version."""
    remote_tuple = parse_version(remote_version)
    current_tuple = parse_version(current_version)

    # Karşılaştırma için uzunlukları eşitle (örn (2, 1) vs (2, 1, 0))
    max_len = max(len(remote_tuple), len(current_tuple))
    r_padded = remote_tuple + (0,) * (max_len - len(remote_tuple))
    c_padded = current_tuple + (0,) * (max_len - len(current_tuple))

    return r_padded > c_padded
