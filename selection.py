"""Compatibility wrapper for selection functions.

This file preserves the original names `get_elites`, `run_tournament`, and
`selection` for scripts that imported them directly. Internally we delegate to
the new implementations in `ga.operators` to keep a single source of truth.
"""
from ga.operators import get_elites, tournament_selection as run_tournament, selection

__all__ = ['get_elites', 'run_tournament', 'selection']


if __name__ == "__main__":
    # minimal demo using the operators module
    import random
    DUMMY_POPULATION = [
        ['D1', 'C1', 'S1', 'C2', 'D2'],
        ['D2', 'C3', 'C4', 'D1'],
        ['D1', 'C5', 'D1'],
        ['D2', 'C1', 'C3', 'S1', 'C2', 'C4', 'D2'],
        ['D1', 'C4', 'C2', 'S1', 'C1', 'C3', 'D1']
    ]
    DUMMY_FITNESS_SCORES = [150.5, 120.2, 210.0, 185.7, 135.9]
    ELITE_SIZE = 1
    TOURNAMENT_SIZE = 2

    selected_parents = selection(DUMMY_POPULATION, DUMMY_FITNESS_SCORES, ELITE_SIZE, TOURNAMENT_SIZE)
    print(f"Selected parents (count={len(selected_parents)}):")
    for p in selected_parents:
        print(p)