"""Population generation utilities for GA.

This module contains a small random population generator that creates delimiter-flat
chromosomes for use in smoke runs. For production, replace with the more advanced
generator in `populasi_awal_final.py` adapted to delimiter encoding.
"""
from typing import List, Dict, Any
import random
from utils import flatten_from_nested


def simple_route_from_depot_customers(depot: str, customers: List[str]) -> List[str]:
    # simple route: depot -> customers in order -> depot
    return [depot] + customers + [depot]


def generate_random_population(depots: List[str], customers: List[str], population_size: int = 10) -> List[List[str]]:
    population: List[List[str]] = []
    for _ in range(population_size):
        remaining = customers.copy()
        random.shuffle(remaining)
        # split into random chunks (random number of routes)
        num_routes = random.randint(1, max(1, min(len(depots), len(customers))))
        # split customers roughly evenly
        chunk_size = max(1, len(customers) // num_routes)
        routes = []
        for i in range(0, len(customers), chunk_size):
            chunk = remaining[i:i+chunk_size]
            depot = random.choice(depots)
            routes.append(simple_route_from_depot_customers(depot, chunk))
        population.append(flatten_from_nested(routes))
    return population
