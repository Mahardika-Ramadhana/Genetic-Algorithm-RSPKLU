"""
MAIN - Genetic Algorithm untuk Electric Vehicle Routing Problem with Satellite stations (EVRP)

Proses: Generate Population -> Fitness -> Crossover -> Mutation -> Selection
Format Kromosom: List dengan delimiter '|' untuk pemisah rute
  Contoh: ['D1', 'C1', 'C2', 'D1', '|', 'D2', 'C3', 'C4', 'D2']
"""

import random
import copy
from generatePopulation import parse_evrp_file, generate_initial_population, generate_initial_chromosome
from fitness import fitness_function
from crossover import bcrc_crossover, crossover_route_based, split_routes, join_routes
from mutation import apply_mutation
from selection import selection, get_elites, run_tournament
from utlis import euclidean_distance, calculate_distance_matrix


class GeneticAlgorithmEVRP:
    """
    Genetic Algorithm untuk menyelesaikan EVRP menggunakan genetic algorithm.
    """
    
    def __init__(self, filepath, population_size=20, generations=50, 
                 elite_size=5, tournament_size=5, mutation_probability=0.1,
                 crossover_probability=0.8, battery_capacity=100, 
                 consumption_rate=1.0, charging_rate=1.0, w1=0.6, w2=0.4):
        """
        Inisialisasi Genetic Algorithm.
        
        Parameters:
        - filepath: Path ke file EVRP
        - population_size: Ukuran populasi
        - generations: Jumlah generasi
        - elite_size: Jumlah elites yang lolos
        - tournament_size: Ukuran tournament
        - mutation_probability: Probabilitas mutasi
        - crossover_probability: Probabilitas crossover
        - battery_capacity: Kapasitas baterai kendaraan
        - consumption_rate: Konsumsi energi per unit jarak
        - charging_rate: Kecepatan charging
        - w1: Weight untuk distance dalam fitness
        - w2: Weight untuk charging time dalam fitness
        """
        self.filepath = filepath
        self.population_size = population_size
        self.generations = generations
        self.elite_size = elite_size
        self.tournament_size = tournament_size
        self.mutation_probability = mutation_probability
        self.crossover_probability = crossover_probability
        self.battery_capacity = battery_capacity
        self.consumption_rate = consumption_rate
        self.charging_rate = charging_rate
        self.w1 = w1
        self.w2 = w2
        
        # Parse file EVRP
        print(f"[INFO] Parse file EVRP: {filepath}")
        self.evrp_data = parse_evrp_file(filepath)
        
        # Hitung distance matrix
        print("[INFO] Menghitung distance matrix...")
        node_coords = self.evrp_data['coords']
        self.distance_matrix = calculate_distance_matrix(node_coords)
        
        # Simpan informasi lokasi untuk mutation dan charging
        self.depot_locations = {f'D{d}': node_coords[d] for d in self.evrp_data['depot']}
        self.customer_locations = {f'C{c}': node_coords[c] for c in self.evrp_data['customers']}
        self.station_locations = {f'S{s}': node_coords[s] for s in self.evrp_data['stations']}
        self.stations_set = set(self.evrp_data['stations'])
        
        # Inisialisasi populasi
        print(f"[INFO] Generate populasi awal dengan ukuran {population_size}...")
        self.population = generate_initial_population(self.evrp_data, population_size)
        
        # Track best solution
        self.best_fitness_history = []
        self.best_solution = None
        self.best_fitness = float('inf')
        self.infeasible_count = 0  # Track infeasible solutions
    
    def evaluate_fitness(self):
        """
        Evaluasi fitness untuk semua kromosom dalam populasi.
        Setiap kromosom yang infeasible akan di-replace dengan random baru.
        
        Returns:
        - fitness_scores: List skor fitness untuk setiap kromosom
        """
        fitness_scores = []
        valid_population = []
        
        for idx, chromosome in enumerate(self.population):
            fitness = fitness_function(
                chromosome,
                distance_matrix=self.distance_matrix,
                node_coords=self.evrp_data['coords'],
                battery_capacity=self.battery_capacity,
                consumption_rate=self.consumption_rate,
                charging_rate=self.charging_rate,
                w1=self.w1,
                w2=self.w2,
                stations=self.stations_set
            )
            
            # Jika infeasible (fitness sangat besar), generate random baru
            if fitness > 1e8:  # Threshold untuk infeasible
                print(f"  [INFEASIBLE] Kromosom {idx} tidak layak (fitness={fitness:.0f}), generate baru...")
                self.infeasible_count += 1
                
                # Generate random kromosom baru
                new_chromosome = generate_initial_chromosome(self.evrp_data)
                self.population[idx] = new_chromosome
                
                # Evaluasi fitness baru
                fitness = fitness_function(
                    new_chromosome,
                    distance_matrix=self.distance_matrix,
                    node_coords=self.evrp_data['coords'],
                    battery_capacity=self.battery_capacity,
                    consumption_rate=self.consumption_rate,
                    charging_rate=self.charging_rate,
                    w1=self.w1,
                    w2=self.w2,
                    stations=self.stations_set
                )
            
            fitness_scores.append(fitness)
        
        return fitness_scores
    
    def perform_crossover(self, parent1, parent2):
        """
        Lakukan crossover antara dua parent.
        
        Parameters:
        - parent1: Kromosom parent 1
        - parent2: Kromosom parent 2
        
        Returns:
        - child: Kromosom hasil crossover (atau copy parent jika tidak crossover)
        """
        if random.random() < self.crossover_probability:
            try:
                # Gunakan BCRC crossover
                child = bcrc_crossover(parent1, parent2, self.distance_matrix)
                return child
            except:
                # Fallback ke copy parent jika crossover gagal
                return copy.deepcopy(parent1)
        else:
            return copy.deepcopy(parent1)
    
    def perform_mutation(self, chromosome):
        """
        Lakukan mutasi pada kromosom.
        
        Parameters:
        - chromosome: Kromosom yang akan dimutasi
        
        Returns:
        - mutated_chromosome: Kromosom setelah mutasi
        """
        mutated = apply_mutation(
            chromosome,
            self.depot_locations,
            self.customer_locations,
            mutation_probability=self.mutation_probability,
            beta=0.2
        )
        return mutated
    
    def run_generation(self):
        """
        Jalankan satu generasi dari genetic algorithm.
        """
        # 1. EVALUATE FITNESS
        print("[STEP 1] Evaluasi fitness...")
        fitness_scores = self.evaluate_fitness()
        
        # Track best solution
        min_fitness = min(fitness_scores)
        min_idx = fitness_scores.index(min_fitness)
        
        # Hanya update jika lebih baik dari sebelumnya
        if min_fitness < self.best_fitness:
            self.best_fitness = min_fitness
            self.best_solution = copy.deepcopy(self.population[min_idx])
            print(f"  [NEW BEST] Fitness: {self.best_fitness:.4f}")
        
        avg_fitness = sum(fitness_scores) / len(fitness_scores)
        self.best_fitness_history.append(self.best_fitness)
        
        print(f"  Min Fitness: {min_fitness:.4f}, Avg Fitness: {avg_fitness:.4f}")
        
        # 2. SELECTION
        print("[STEP 2] Selection (Elitism + Tournament)...")
        new_parents = selection(
            self.population,
            fitness_scores,
            elite_size=self.elite_size,
            tournament_size=self.tournament_size
        )
        
        # 3. CROSSOVER & MUTATION
        print("[STEP 3] Crossover dan Mutation...")
        new_population = []
        
        # Pertahankan elites
        elites = get_elites(self.population, fitness_scores, self.elite_size)
        new_population.extend(copy.deepcopy(elites))
        
        # Generate offspring dari parents
        attempts = 0
        max_attempts = self.population_size * 2
        
        while len(new_population) < self.population_size and attempts < max_attempts:
            attempts += 1
            
            # Pilih dua parents secara random dari new_parents
            parent1 = copy.deepcopy(random.choice(new_parents))
            parent2 = copy.deepcopy(random.choice(new_parents))
            
            # Crossover
            child = self.perform_crossover(parent1, parent2)
            
            # Mutation
            child = self.perform_mutation(child)
            
            new_population.append(child)
        
        # Ensure population size tepat
        self.population = new_population[:self.population_size]
        
        # Jika population kurang dari target, generate random
        while len(self.population) < self.population_size:
            self.population.append(generate_initial_chromosome(self.evrp_data))
    
    def run(self):
        """
        Jalankan genetic algorithm untuk jumlah generasi yang ditentukan.
        """
        print("\n" + "="*80)
        print("GENETIC ALGORITHM - ELECTRIC VEHICLE ROUTING PROBLEM (EVRP)")
        print("="*80)
        print(f"File: {self.filepath}")
        print(f"Vehicles: {self.evrp_data['vehicles']}")
        print(f"Customers: {len(self.evrp_data['customers'])}")
        print(f"Stations: {len(self.evrp_data['stations'])}")
        print(f"Population Size: {self.population_size}")
        print(f"Generations: {self.generations}")
        print(f"Elite Size: {self.elite_size}")
        print(f"Tournament Size: {self.tournament_size}")
        print(f"Battery Capacity: {self.battery_capacity}")
        print("="*80 + "\n")
        
        for gen in range(1, self.generations + 1):
            print(f"\n[GEN {gen}/{self.generations}]")
            print("-" * 40)
            
            self.run_generation()
            
            print(f"Best Fitness (Gen {gen}): {self.best_fitness:.4f}")
            routes_count = self.get_routes_from_solution()
            print(f"Routes in Solution: {len(routes_count)}, Vehicles: {self.evrp_data['vehicles']}")
        
        return self.best_solution, self.best_fitness
    
    def print_results(self):
        """
        Cetak hasil akhir dari genetic algorithm dengan statistik lengkap.
        """
        print("\n" + "="*80)
        print("HASIL AKHIR")
        print("="*80)
        print(f"Best Fitness: {self.best_fitness:.4f}")
        print(f"Infeasible Solutions Eliminated: {self.infeasible_count}")
        print(f"Best Fitness History (per generasi):")
        
        # Print history dengan formatting
        for i, fit in enumerate(self.best_fitness_history, 1):
            if i % 10 == 0:
                print(f"  Gen {i}: {fit:.4f}")
        
        print(f"\nBest Solution (Kromosom): {self.best_solution}")
        print("="*80)
    
    def get_routes_from_solution(self):
        """
        Parse best solution menjadi daftar rute yang mudah dibaca.
        
        Returns:
        - list: Daftar rute dalam format yang mudah dibaca
        """
        if not self.best_solution:
            return []
        
        routes = split_routes(self.best_solution)
        readable_routes = []
        for i, route in enumerate(routes, 1):
            route_str = ' → '.join(route)
            readable_routes.append(f"Route {i}: {route_str}")
        
        return readable_routes


def main():
    """
    Fungsi utama untuk menjalankan genetic algorithm.
    """
    # Konfigurasi
    filepath = "data/E-n32-k6-s7-edited.evrp"  # Sesuaikan dengan file yang ingin digunakan
    
    ga = GeneticAlgorithmEVRP(
        filepath=filepath,
        population_size=20,
        generations=50,
        elite_size=5,
        tournament_size=5,
        mutation_probability=0.1,
        crossover_probability=0.8,
        battery_capacity=300,  # Increased dari 100
        consumption_rate=0.5,  # Decreased dari 1.0
        charging_rate=1.0,
        w1=0.6,
        w2=0.4
    )
    
    # Jalankan GA
    best_solution, best_fitness = ga.run()
    
    # Print hasil
    ga.print_results()
    
    # Print routes
    print("\n" + "="*80)
    print("RUTE-RUTE DALAM SOLUSI TERBAIK:")
    print("="*80)
    routes = ga.get_routes_from_solution()
    for route in routes:
        print(route)
    print("="*80)


if __name__ == "__main__":
    main()
