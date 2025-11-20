"""Fitness evaluator: simulates battery and charging for delimiter-flat chromosomes."""
from typing import List, Dict, Tuple, Any
from utils import split_routes, get_distance, INFEASIBLE_PENALTY


def fitness_function(chromosome: List[str], distance_matrix: Dict[Tuple[str, str], float],
                     battery_capacity: float = 100.0, consumption_rate: float = 1.0,
                     charging_rate: float = 1.0, w_distance: float = 0.6, w_charging: float = 0.4) -> float:
    """Compute fitness: weighted sum of total distance and charging time.

    Returns a smaller-is-better fitness. Infeasible solutions get a large penalty.
    Chromosome encoding: delimiter-flat list with 'S*' representing charging stations,
    'D*' depots and 'C*' customers.
    """
    total_distance = 0.0
    total_charging_time = 0.0

    routes = split_routes(chromosome)

    for route in routes:
        battery = battery_capacity
        for i in range(len(route) - 1):
            a, b = route[i], route[i + 1]
            dist = get_distance(a, b, distance_matrix)
            if dist == float('inf'):
                return INFEASIBLE_PENALTY
            total_distance += dist
            needed_energy = dist * consumption_rate

            # If current node is charging station, charge minimally to reach next station/depot
            if a.startswith('S'):
                # lookahead to next S or D
                energy_needed_to_next = 0.0
                for j in range(i, len(route) - 1):
                    u, v = route[j], route[j + 1]
                    d2 = get_distance(u, v, distance_matrix)
                    if d2 == float('inf'):
                        return INFEASIBLE_PENALTY
                    energy_needed_to_next += d2 * consumption_rate
                    if route[j + 1].startswith('S') or route[j + 1].startswith('D'):
                        break
                required_energy = max(0.0, energy_needed_to_next - battery)
                charge_time = required_energy / charging_rate
                total_charging_time += charge_time
                battery += required_energy
                if battery > battery_capacity:
                    battery = battery_capacity

            if battery < needed_energy:
                # insufficient battery to travel (invalid)
                return INFEASIBLE_PENALTY

            battery -= needed_energy

    # normalization
    D = total_distance / 100.0
    C = total_charging_time / 100.0
    fitness = w_distance * D + w_charging * C
    return fitness
