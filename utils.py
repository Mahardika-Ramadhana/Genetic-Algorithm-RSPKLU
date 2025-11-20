"""Utilities for Genetic Algorithm MDVRP / SPKLU project.

This module centralizes helpers used across selection, mutation, crossover,
population generation and fitness evaluation:
- loading nodes from CSV
- building a canonical distance matrix (tuple-keyed)
- flexible distance lookup (supports dict-of-dict and tuple-keyed)
- chromosome encoding/decoding helpers (delimiter '|' encoding)
- small constants (penalty)

Keep functions pure and well-typed so other modules can import them.
"""
from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from typing import Dict, Tuple, List, Any, Optional

# Penalty used for infeasible solutions (minimization problem)
INFEASIBLE_PENALTY = 1e6


def load_nodes_from_csv(filename: str, delimiter: str = ';') -> Dict[str, Dict[str, Any]]:
    """Load nodes from a CSV file.

    Returns a mapping node_id -> {'x': float, 'y': float, 'demand': int}
    Node id is returned as string (preserves values like 'D1' or numeric indices).
    The CSV is expected to have headers that include at least columns named
    'index' (or 'id'), 'x', 'y' and optionally 'Demand' or 'demand'. The function
    is permissive and will attempt to parse common formats.
    """
    nodes: Dict[str, Dict[str, Any]] = {}
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        for row in reader:
            # find id column
            node_id = None
            for k in ('index', 'id', 'node', 'name'):
                if k in row and row[k] not in (None, ''):
                    node_id = str(row[k]).strip()
                    break

            if node_id is None:
                # try first column
                try:
                    node_id = str(next(iter(row.values()))).strip()
                except StopIteration:
                    continue

            try:
                x_raw = row.get('x') or row.get('X') or row.get('lon') or row.get('longitude')
                y_raw = row.get('y') or row.get('Y') or row.get('lat') or row.get('latitude')
                x = float(str(x_raw).replace(',', '.'))
                y = float(str(y_raw).replace(',', '.'))
            except Exception:
                # skip malformed rows
                continue

            demand_raw = row.get('Demand') or row.get('demand') or row.get('d') or 0
            try:
                demand = int(str(demand_raw))
            except Exception:
                try:
                    demand = int(float(str(demand_raw).replace(',', '.')))
                except Exception:
                    demand = 0

            nodes[node_id] = {'x': x, 'y': y, 'demand': demand}

    return nodes


def build_distance_matrix(nodes: Dict[str, Dict[str, Any]], symmetric: bool = True) -> Dict[Tuple[str, str], float]:
    """Build a tuple-keyed distance matrix from nodes mapping.

    nodes: mapping node_id -> {'x': float, 'y': float, ...}
    Returns dict[(a,b)] -> euclidean_distance
    If symmetric=True, (a,b) == (b,a) distance is stored by computing once.
    """
    dist: Dict[Tuple[str, str], float] = {}
    keys = list(nodes.keys())
    for i, a in enumerate(keys):
        ax, ay = nodes[a]['x'], nodes[a]['y']
        for j in range(i + 1, len(keys)):
            b = keys[j]
            bx, by = nodes[b]['x'], nodes[b]['y']
            d = math.hypot(ax - bx, ay - by)
            dist[(a, b)] = d
            if symmetric:
                dist[(b, a)] = d

        # self distance
        dist[(a, a)] = 0.0

    return dist


def get_distance(a: str, b: str, distance_matrix: Any, default: float = float('inf')) -> float:
    """Retrieve distance between a and b from flexible distance_matrix.

    Supports two common shapes:
    - dict with tuple keys, e.g. distance_matrix[(a,b)] = 12.3
    - nested dict, e.g. distance_matrix[a][b] = 12.3

    Returns default if no entry found.
    """
    if a == b:
        return 0.0

    # tuple-keyed dict
    try:
        if (a, b) in distance_matrix:
            return distance_matrix[(a, b)]
    except Exception:
        pass

    # nested dict-like
    try:
        if a in distance_matrix and b in distance_matrix[a]:
            return distance_matrix[a][b]
        if b in distance_matrix and a in distance_matrix[b]:
            return distance_matrix[b][a]
    except Exception:
        pass

    return default


def split_routes(chromosome: List[str], delimiter: str = '|') -> List[List[str]]:
    """Split a delimiter-flat chromosome into list of routes.

    Example: ['D1','C1','D1','|','D2','C2','D2'] -> [['D1','C1','D1'], ['D2','C2','D2']]
    """
    routes: List[List[str]] = []
    cur: List[str] = []
    for gene in chromosome:
        if gene == delimiter:
            if cur:
                routes.append(cur.copy())
                cur = []
        else:
            cur.append(gene)
    if cur:
        routes.append(cur.copy())
    return routes


def join_routes(routes: List[List[str]], delimiter: str = '|') -> List[str]:
    """Join nested routes into delimiter-flat chromosome.

    Example: [['D1','C1','D1'], ['D2','C2','D2']] -> ['D1','C1','D1','|','D2','C2','D2']
    """
    chrom: List[str] = []
    for i, r in enumerate(routes):
        if i > 0:
            chrom.append(delimiter)
        chrom.extend(r)
    return chrom


def flatten_from_nested(chromosome_nested: List[List[str]], delimiter: str = '|') -> List[str]:
    """Alias to join_routes for clarity."""
    return join_routes(chromosome_nested, delimiter=delimiter)


def nested_from_flat(chromosome_flat: List[str], delimiter: str = '|') -> List[List[str]]:
    """Alias to split_routes for clarity."""
    return split_routes(chromosome_flat, delimiter=delimiter)


def rebuild_chromosome_from_routes(routes: List[dict]) -> List[str]:
    """Compatibility helper used by older code: expects routes as dict with 'full_route'.

    Each route dict should include 'full_route' which is a list of nodes.
    Returns delimiter-flat chromosome.
    """
    chrom: List[str] = []
    for i, route in enumerate(routes):
        if i > 0:
            chrom.append('|')
        chrom.extend(route.get('full_route', []))
    return chrom


def euclidean_distance(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    """Simple 2D Euclidean distance between coordinate tuples."""
    return math.hypot(a[0] - b[0], a[1] - b[1])


@dataclass
class GAConfig:
    population_size: int = 50
    generations: int = 200
    elite_size: int = 2
    tournament_size: int = 3
    crossover_rate: float = 0.8
    mutation_rate: float = 0.1
    battery_capacity: float = 100.0
    consumption_rate: float = 1.0
    charging_rate: float = 1.0
    w_distance: float = 0.6
    w_charging: float = 0.4


__all__ = [
    'load_nodes_from_csv',
    'build_distance_matrix',
    'get_distance',
    'split_routes',
    'join_routes',
    'flatten_from_nested',
    'nested_from_flat',
    'rebuild_chromosome_from_routes',
    'euclidean_distance',
    'INFEASIBLE_PENALTY',
    'GAConfig',
]
