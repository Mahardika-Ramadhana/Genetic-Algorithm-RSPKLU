"""Selection, crossover and mutation operators for GA.

Functions expect delimiter-flat chromosome encoding (list[str]) where '|' separates routes.
"""
from typing import List, Tuple, Dict, Any
import random
import copy
from utils import split_routes, join_routes, get_distance


def get_elites(population: List[List[str]], fitness_scores: List[float], elite_size: int) -> List[List[str]]:
    paired = list(zip(population, fitness_scores))
    paired.sort(key=lambda x: x[1])
    return [p for p, _ in paired[:elite_size]]


def tournament_selection(population: List[List[str]], fitness_scores: List[float], tournament_size: int) -> List[str]:
    indices = random.sample(range(len(population)), k=min(tournament_size, len(population)))
    best = None
    best_score = float('inf')
    for i in indices:
        if fitness_scores[i] < best_score:
            best_score = fitness_scores[i]
            best = population[i]
    return best


def selection(population: List[List[str]], fitness_scores: List[float], elite_size: int, tournament_size: int) -> List[List[str]]:
    parents: List[List[str]] = []
    parents.extend(get_elites(population, fitness_scores, elite_size))
    remaining = len(population) - elite_size
    for _ in range(remaining):
        parents.append(tournament_selection(population, fitness_scores, tournament_size))
    return parents


# ---- BCRC crossover (from notebook) adapted ----
def remove_customer_routes(routes: List[List[str]], customer: str) -> List[List[str]]:
    return [[x for x in r if x != customer] for r in routes]


def insertion_cost(route: List[str], customer: str, dist: Dict[Tuple[str, str], float]) -> Tuple[float, int]:
    if len(route) < 2:
        return 0.0, 0
    best_cost = float('inf')
    best_pos = 0
    for i in range(len(route) - 1):
        a, b = route[i], route[i+1]
        cost_before = get_distance(a, b, dist)
        cost_after = get_distance(a, customer, dist) + get_distance(customer, b, dist)
        delta = cost_after - cost_before
        if delta < best_cost:
            best_cost = delta
            best_pos = i + 1
    return best_cost, best_pos


def bcrc_crossover(chrom1: List[str], chrom2: List[str], dist: Dict[Tuple[str, str], float]) -> List[str]:
    p1 = copy.deepcopy(chrom1)
    p2 = copy.deepcopy(chrom2)
    routes1 = split_routes(p1)
    routes2 = split_routes(p2)
    all_customers = [x for r in routes1 for x in r if x.startswith('C')]
    if not all_customers:
        return chrom2.copy()
    customer = random.choice(all_customers)
    child_routes = remove_customer_routes(routes2, customer)
    best_global_cost = float('inf')
    best_route_idx = None
    best_insert_pos = None
    for idx, route in enumerate(child_routes):
        if len(route) < 2:
            continue
        cost, pos = insertion_cost(route, customer, dist)
        if cost < best_global_cost:
            best_global_cost = cost
            best_route_idx = idx
            best_insert_pos = pos
    if best_route_idx is not None:
        child_routes[best_route_idx].insert(best_insert_pos, customer)
    else:
        for idx, route in enumerate(child_routes):
            if len(route) >= 2:
                child_routes[idx].insert(1, customer)
                break
    return join_routes(child_routes)


# ---- Mutation (simpler variant) ----
def apply_mutation(chromosome: List[str], mutation_rate: float = 0.1) -> List[str]:
    # simple swap mutation within a route
    if random.random() > mutation_rate:
        return chromosome
    routes = split_routes(chromosome)
    # pick a random route with at least two customers (excluding depots)
    route_idx = None
    for _ in range(5):
        i = random.randrange(len(routes))
        customers = [x for x in routes[i] if x.startswith('C')]
        if len(customers) >= 2:
            route_idx = i
            break
    if route_idx is None:
        return chromosome
    # perform swap on customer positions within chosen route
    route = routes[route_idx]
    cust_positions = [i for i, g in enumerate(route) if g.startswith('C')]
    a, b = random.sample(cust_positions, 2)
    route[a], route[b] = route[b], route[a]
    routes[route_idx] = route
    return join_routes(routes)


# ---- Advanced mutation wrapper (uses legacy `mutation.py` implementation) ----
def apply_mutation_advanced(chromosome: List[str], depot_locations: Dict[str, tuple], customer_locations: Dict[str, tuple], mutation_probability: float = 0.1, beta: float = 0.2) -> List[str]:
    """Use existing sophisticated mutation logic from `mutation.py` if available.

    This function imports the original `apply_mutation` from `mutation.py` which
    implements inter-depot and intra-depot strategies. It provides a thin wrapper
    so callers can choose between the simple mutation above or the advanced one.
    """
    try:
        import mutation as mut
    except Exception:
        # fallback to simple mutation if module not importable
        return apply_mutation(chromosome, mutation_rate=mutation_probability)

    # the legacy mutation expects depot/customer dicts and returns a new chromosome
    return mut.apply_mutation(chromosome, depot_locations, customer_locations, mutation_probability=mutation_probability, beta=beta)
