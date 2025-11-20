"""Minimal GA runner (smoke test) for Rute SPKLU problem.

This script builds a tiny synthetic problem and runs a few GA generations to
demonstrate end-to-end wiring of utils, ga.population, ga.operators and ga.evaluator.
"""
from ga.population import generate_random_population
from ga.operators import selection, bcrc_crossover, apply_mutation
from ga.evaluator import fitness_function
from utils import build_distance_matrix, load_nodes_from_csv

import argparse
import random
import os


def synthetic_nodes():
    # create small synthetic nodes. IDs: D1, S1, C1..C5
    nodes = {
        'D1': {'x': 0.0, 'y': 0.0, 'demand': 0},
        'S1': {'x': 5.0, 'y': 0.0, 'demand': 0},
        'C1': {'x': 2.0, 'y': 1.0, 'demand': 1},
        'C2': {'x': 2.5, 'y': -1.0, 'demand': 1},
        'C3': {'x': 4.0, 'y': 1.5, 'demand': 1},
        'C4': {'x': -1.0, 'y': -0.5, 'demand': 1},
        'C5': {'x': -2.0, 'y': 1.0, 'demand': 1},
    }
    return nodes


def run_smoke():
    random.seed(1)
    nodes = synthetic_nodes()
    dist = build_distance_matrix(nodes)

    depots = ['D1']
    customers = ['C1', 'C2', 'C3', 'C4', 'C5']

    pop = generate_random_population(depots, customers, population_size=8)

    generations = 20
    elite_size = 1
    tournament_size = 3

    best = None
    best_score = float('inf')

    for g in range(generations):
        fitnesses = [fitness_function(ch, dist) for ch in pop]
        # track best
        for ch, f in zip(pop, fitnesses):
            if f < best_score:
                best_score = f
                best = ch

        print(f"Gen {g}: best={best_score:.6f}")

        parents = selection(pop, fitnesses, elite_size=elite_size, tournament_size=tournament_size)

        # crossover
        next_pop = []
        while len(next_pop) < len(pop):
            a = random.choice(parents)
            b = random.choice(parents)
            child = bcrc_crossover(a, b, dist)
            child = apply_mutation(child, mutation_rate=0.2)
            next_pop.append(child)

        pop = next_pop

    print('\nBest chromosome:', best)
    print('Best fitness:', best_score)


def run_from_csv(csv_path: str):
    """Run GA using nodes loaded from a CSV file.

    The loader expects node IDs in the CSV that start with 'D' for depot,
    'S' for charging stations and 'C' for customers. If those prefixes are
    not present, the function will attempt to infer depots/customers heuristically.
    """
    nodes = load_nodes_from_csv(csv_path)
    if not nodes:
        print(f"No nodes loaded from {csv_path}; falling back to synthetic dataset.")
        return run_smoke()

    dist = build_distance_matrix(nodes)

    # infer roles by prefix (D=depot, S=spklu, C=customer)
    depots = [n for n in nodes.keys() if str(n).upper().startswith('D')]
    spklus = [n for n in nodes.keys() if str(n).upper().startswith('S')]
    customers = [n for n in nodes.keys() if str(n).upper().startswith('C')]

    # fallback heuristics
    if not depots:
        # if no D* found, take first node as depot
        depots = [next(iter(nodes.keys()))]
    if not customers:
        # all non-depot/non-spklu nodes are customers
        customers = [n for n in nodes.keys() if n not in depots + spklus]

    print(f"Using {len(depots)} depots, {len(spklus)} SPKLU, {len(customers)} customers from {csv_path}")

    pop = generate_random_population(depots, customers, population_size=20)

    generations = 50
    elite_size = 2
    tournament_size = 3

    best = None
    best_score = float('inf')

    for g in range(generations):
        fitnesses = [fitness_function(ch, dist) for ch in pop]
        for ch, f in zip(pop, fitnesses):
            if f < best_score:
                best_score = f
                best = ch
        print(f"Gen {g}: best={best_score:.6f}")
        parents = selection(pop, fitnesses, elite_size=elite_size, tournament_size=tournament_size)
        next_pop = []
        while len(next_pop) < len(pop):
            a = random.choice(parents)
            b = random.choice(parents)
            child = bcrc_crossover(a, b, dist)
            child = apply_mutation(child, mutation_rate=0.2)
            next_pop.append(child)
        pop = next_pop

    print('\nBest chromosome:', best)
    print('Best fitness:', best_score)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run GA for Rute SPKLU (smoke or real CSV)')
    parser.add_argument('--csv', '-c', help='Path to nodes CSV (optional). If omitted, runs synthetic smoke example.')
    args = parser.parse_args()

    if args.csv and os.path.exists(args.csv):
        run_from_csv(args.csv)
    else:
        if args.csv:
            print(f"CSV path provided but not found: {args.csv}. Running synthetic smoke instead.")
        run_smoke()
