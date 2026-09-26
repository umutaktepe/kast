"""Version specification and semantic version comparison utilities for Kast."""

import re
from typing import Tuple

__version__ = "2.1.1"


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
