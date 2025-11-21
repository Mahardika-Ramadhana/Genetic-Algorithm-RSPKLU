"""
main_dika.py

Minimal GA orchestration template for Dika.

This script is intentionally lightweight and defensive: it will attempt to
use project functions (like `generate_initial_population`) if present, but
will fall back to small dummy data if necessary. It demonstrates how to wire
`selection.selection` and `mutation.apply_mutation` together and provides a
place to expand into a full GA loop.

Usage: python main_dika.py
"""
import logging
import random
from typing import List

import main_asli
import data_prep
import utlis

from populasi_awal_final import generate_initial_population, MDVRPConfig
from selection import selection
from mutation import apply_mutation
from fitness import fitness_function


logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def run_pipeline():
    cfg = main_asli.config
    logger.info("Preparing dataset (data cleaning)")
    cleaned_csv, nodes = data_prep.prepare_dataset(cfg.get('csv_file', 'data_koordinat.csv'))
    logger.info(f"Cleaned CSV: {cleaned_csv} (nodes: {len(nodes)})")

    # Build MDVRPConfig using the original CSV file (populasi_awal_final expects
    # the original semicolon-delimited format and specific header names).
    original_csv = cfg.get('csv_file', 'data_koordinat.csv')
    mdcfg = MDVRPConfig(original_csv,
                        depot_indices=cfg.get('depot_indices'),
                        spklu_indices=cfg.get('spklu_indices'),
                        customer_indices=None,
                        vehicle_capacity=cfg.get('vehicle_capacity', 100))

    logger.info("Generating initial population using populasi_awal_final.generate_initial_population()")
    population = generate_initial_population(mdcfg, pop_size=cfg.get('pop_size', 20), use_spklu=True)
    logger.info(f"Generated population size: {len(population)}")
    if not population:
        raise RuntimeError(
            "Initial population is empty. Check `populasi_awal_final.generate_initial_population` "
            "configuration and input CSV. Configuration: " + str(cfg)
        )

    # Evaluate initial fitness
    fitness_scores = [fitness_function(ind, distance_matrix=None, node_coords={i: (nodes[i]['x'], nodes[i]['y']) for i in nodes}) for ind in population]

    # Main GA loop
    generations = cfg.get('generations', 50)
    for gen in range(1, generations + 1):
        logger.info(f"Generation {gen}/{generations}")

        parents = selection(population, fitness_scores, cfg.get('elite_size', 1), cfg.get('tournament_size', 2))

        # Reproduce: simple pipeline using selection + mutation + crossover handled inside populate function
        next_pop = list(parents)
        while len(next_pop) < cfg.get('pop_size', 20):
            # randomly pick parent and apply mutation
            p = random.choice(parents).copy()
            mutated = apply_mutation(p, depot_locations={d: (nodes[d]['x'], nodes[d]['y']) for d in cfg.get('depot_indices', []) if d in nodes},
                                     customer_locations={c: (nodes[c]['x'], nodes[c]['y']) for c in nodes},
                                     mutation_probability=cfg.get('mutation_prob', 0.2))
            next_pop.append(mutated)

        population = next_pop[:cfg.get('pop_size', 20)]
        fitness_scores = [fitness_function(ind, distance_matrix=None, node_coords={i: (nodes[i]['x'], nodes[i]['y']) for i in nodes}) for ind in population]

        # report best
        best_idx = min(range(len(population)), key=lambda i: fitness_scores[i])
        logger.info(f" Best fitness: {fitness_scores[best_idx]:.4f}")


if __name__ == '__main__':
    run_pipeline()
