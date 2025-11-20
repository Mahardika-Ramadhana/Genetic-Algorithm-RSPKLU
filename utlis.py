
"""Compatibility shim for older code that imported `utlis`.

This file used to contain minimal helper stubs. We now forward the common
helpers to `utils.py` so older imports keep working while the canonical
implementations live in `utils.py`.
"""
from typing import Any
from utils import load_nodes_from_csv, build_distance_matrix, get_distance


def load_data(file_path: str, delimiter: str = ';') -> Any:
    """Backward-compatible wrapper around `utils.load_nodes_from_csv`.

    Returns the same mapping produced by `load_nodes_from_csv`.
    """
    return load_nodes_from_csv(file_path, delimiter=delimiter)


def get_dist(a: str, b: str, distance_matrix: Any):
    """Wrapper around `utils.get_distance` for legacy calls."""
    return get_distance(a, b, distance_matrix)