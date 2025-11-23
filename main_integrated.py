# file: main_integrated.py
import logging
import random
import math
import sys
import time

# --- IMPORT MODUL CUSTOM ---
from configuration import config
from generatePopulation import parse_evrp_file, generate_initial_population
from selection import selection
from crossover import bcrc_crossover
from mutation import apply_mutation
from fitness import fitness_function

# Import Repair (Wajib ada file repair.py)
try:
    from repair import repair_chromosome
except ImportError:
    print("\n[CRITICAL ERROR] File 'repair.py' tidak ditemukan!")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

def build_distance_matrix(coords):
    """
    Pre-calculate jarak antar SEMUA titik (Depot, Customer, Station).
    Hasilnya disimpan di memori agar tidak perlu hitung ulang terus-menerus.
    """
    dist_matrix = {}
    nodes = list(coords.keys())
    total_nodes = len(nodes)
    print(f"    >> Membangun Matriks Jarak untuk {total_nodes} titik...")
    
    for i in nodes:
        dist_matrix[i] = {}
        for j in nodes:
            if i == j:
                dist_matrix[i][j] = 0.0
            else:
                x1, y1 = coords[i]
                x2, y2 = coords[j]
                dist_matrix[i][j] = math.sqrt((x1 - x2)**2 + (y1 - y2)**2)
    return dist_matrix

def prepare_data_structures(evrp_data):
    raw_coords = evrp_data['coords']
    depots = evrp_data['depot']
    customers = evrp_data['customers']
    stations = evrp_data['stations']

    string_coords = {}
    depot_locs = {}
    customer_locs = {}
    station_locs = {}
    
    # Mapping ID integer ke String (D1, C2, S1001)
    for d_id in depots:
        key = f"D{d_id}"
        string_coords[key] = raw_coords[d_id]
        depot_locs[key] = raw_coords[d_id]

    for c_id in customers:
        key = f"C{c_id}"
        string_coords[key] = raw_coords[c_id]
        customer_locs[key] = raw_coords[c_id]

    for s_id in stations:
        key = f"S{s_id}"
        string_coords[key] = raw_coords[s_id]
        station_locs[key] = raw_coords[s_id]

    return string_coords, depot_locs, customer_locs, station_locs

def run_integrated_ga():
    # ---------------------------------------------------------
    # 1. LOAD DATASET
    # ---------------------------------------------------------
    filename = config.get('evrp_file', 'X-n1012-k43-s5-edited.evrp')
    logger.info(f"\n=== MEMULAI GA EVRP (OPTIMIZED): {filename} ===")
    
    try:
        evrp_data = parse_evrp_file(filename)
    except FileNotFoundError:
        logger.error(f"[ERROR] File {filename} tidak ditemukan.")
        return

    # Parameter Baterai
    battery_cap = evrp_data.get('energy_capacity', 2536)
    energy_consumption = evrp_data.get('energy_consumption', 1.0)

    # ---------------------------------------------------------
    # 2. PERSIAPAN DATA & MATRIX (Optimasi Kecepatan)
    # ---------------------------------------------------------
    logger.info("--- Menyiapkan Data & Menghitung Jarak ---")
    all_coords, depot_locs, customer_locs, station_locs = prepare_data_structures(evrp_data)
    
    # Pre-compute distances
    dist_matrix = build_distance_matrix(all_coords)
    station_ids = list(station_locs.keys())

    # ---------------------------------------------------------
    # 3. GENERATE POPULASI AWAL
    # ---------------------------------------------------------
    # Gunakan pop_size kecil dulu (misal 15 atau 20) di config agar cepat
    pop_size = config.get('pop_size', 15) 
    logger.info(f"--- Membangkitkan Populasi Awal (Size: {pop_size}) ---")
    
    population = generate_initial_population(evrp_data, population_size=pop_size)
    
    # ---------------------------------------------------------
    # 4. INITIAL REPAIR (Agar rute awal valid)
    # ---------------------------------------------------------
    logger.info("--- Melakukan Smart Repair pada Populasi Awal ---")
    repaired_pop = []
    start_time = time.time()
    
    for i, chrom in enumerate(population):
        # Progress Indicator
        sys.stdout.write(f"\r    >> Memproses Individu {i+1}/{pop_size} ")
        sys.stdout.flush()
        
        # Panggil fungsi repair yang sudah dioptimasi (pakai dist_matrix)
        fixed_chrom = repair_chromosome(
            chrom, 
            dist_matrix, 
            station_ids, 
            battery_cap, 
            energy_consumption
        )
        repaired_pop.append(fixed_chrom)
    
    elapsed = time.time() - start_time
    print(f"\n    >> Selesai dalam {elapsed:.2f} detik.")
    population = repaired_pop

    # ---------------------------------------------------------
    # 5. LOOP GENERASI (MAIN GA LOOP)
    # ---------------------------------------------------------
    generations = config.get('generations', 50)
    w1 = config.get('w1', 0.6)
    w2 = config.get('w2', 0.4)
    
    logger.info(f"\n--- Memulai Evolusi ({generations} Generasi) ---")

    for gen in range(1, generations + 1):
        # A. Hitung Fitness
        fitness_scores = []
        for chrom in population:
            f = fitness_function(
                chrom, 
                distance_matrix=dist_matrix, # Kirim matrix agar fitness juga cepat
                node_coords=all_coords,
                battery_capacity=battery_cap,
                consumption_rate=energy_consumption,
                w1=w1, w2=w2
            )
            fitness_scores.append(f)

        # Logging
        best_fitness = min(fitness_scores)
        avg_fitness = sum(fitness_scores) / len(fitness_scores)
        print(f"Gen {gen:3d}/{generations} | Best: {best_fitness:10.4f} | Avg: {avg_fitness:10.4f}")

        # B. Seleksi
        parents = selection(population, fitness_scores, config['elite_size'], config['tournament_size'])

        # C. Reproduksi
        next_population = parents[:]
        
        while len(next_population) < pop_size:
            p1 = random.choice(parents)
            p2 = random.choice(parents)
            
            # 1. Crossover
            child_chrom = bcrc_crossover(p1, p2, dist_matrix)
            
            # 2. Mutasi
            child_mutated = apply_mutation(
                child_chrom, 
                depot_locations=depot_locs,
                customer_locations=customer_locs,
                station_locations=station_locs, 
                mutation_probability=config['mutation_prob']
            )
            
            # 3. Repair (Wajib dilakukan setelah mutasi/crossover)
            child_repaired = repair_chromosome(
                child_mutated,
                dist_matrix,
                station_ids,
                battery_cap,
                energy_consumption
            )
            
            next_population.append(child_repaired)

        population = next_population[:pop_size]

    # ---------------------------------------------------------
    # 6. HASIL AKHIR
    # ---------------------------------------------------------
    final_scores = [fitness_function(c, distance_matrix=dist_matrix, battery_capacity=battery_cap, w1=w1, w2=w2) for c in population]
    best_idx = final_scores.index(min(final_scores))
    
    print("\n" + "="*40)
    print("         HASIL AKHIR TERBAIK")
    print("="*40)
    print(f"Fitness Score : {final_scores[best_idx]:.4f}")
    print(f"Kromosom      : {population[best_idx]}")
    print("="*40)

if __name__ == '__main__':
    run_integrated_ga()