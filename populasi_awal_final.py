import random
from utlis import get_demand

# ----- FUNGSI GENERATE POPULASI AWAL -----
def generate_initial_population(depot_indices, spklu_indices, customer_indices, 
                                vehicle_capacity, pop_size=10, use_spklu=True):
    """
    Generate populasi awal untuk Algoritma Genetika pada MDVRP.
    
    Chromosome representation:
    - Setiap chromosome adalah list of routes
    - Setiap route: [Depot_Awal] + [Customers] + [SPKLU (opsional)] + [Depot_Akhir]
    - Customers didistribusikan ke multiple routes berdasarkan kapasitas
    
    Args:
        depot_indices: List indeks depot
        spklu_indices: List indeks SPKLU
        customer_indices: List indeks customer
        vehicle_capacity: Kapasitas kendaraan
        pop_size: Jumlah chromosome dalam populasi
        use_spklu: Apakah menggunakan SPKLU dalam rute
    
    Returns:
        List of chromosomes (populasi awal)
    """
    population = []
    population_set = set()
    
    max_attempts = pop_size * 10
    attempts = 0
    
    while len(population) < pop_size and attempts < max_attempts:
        attempts += 1
        chromosome = []
        remaining_customers = customer_indices.copy()
        random.shuffle(remaining_customers)
        
        # Assign customers ke rute berdasarkan kapasitas
        while remaining_customers:
            # Pilih depot awal dan akhir secara random
            start_depot = random.choice(depot_indices)
            end_depot = random.choice(depot_indices)
            
            # Bentuk rute dengan memperhatikan kapasitas
            route_customers = []
            current_demand = 0
            
            # Masukkan customers selama tidak melebihi kapasitas
            # Asumsi: setiap customer memiliki demand = 1 (bisa disesuaikan)
            for customer in remaining_customers[:]:
                customer_demand = get_demand(customer)  # Sesuaikan dengan data demand sebenarnya jika ada
                if current_demand + customer_demand <= vehicle_capacity:
                    route_customers.append(customer)
                    current_demand += customer_demand
            
            # Jika tidak ada customer yang bisa ditambahkan, ambil satu
            if not route_customers and remaining_customers:
                route_customers.append(remaining_customers[0])
            
            if not route_customers:
                break
            
            # Bentuk rute lengkap
            if use_spklu and spklu_indices:
                spklu = random.choice(spklu_indices)
                route = [start_depot] + route_customers + [spklu] + [end_depot]
            else:
                route = [start_depot] + route_customers + [end_depot]
            
            chromosome.append(route)
            
            # Hapus customers yang sudah diassign
            for customer in route_customers:
                remaining_customers.remove(customer)
        
        # Validasi: semua customers harus terassign
        if len(remaining_customers) == 0 and len(chromosome) > 0:
            chromosome_tuple = tuple(tuple(route) for route in chromosome)
            
            if chromosome_tuple not in population_set:
                population.append(chromosome)
                population_set.add(chromosome_tuple)
    
    return population


# ----- CONTOH PENGGUNAAN -----
if __name__ == "__main__":
    # Konfigurasi
    DEPOT_INDICES = ['D1', 'D2']
    SPKLU_INDICES = ['S1', 'S2']
    CUSTOMER_INDICES = ['C1', 'C2', 'C3', 'C4', 'C5']
    VEHICLE_CAPACITY = 3
    POP_SIZE = 5
    
    # Generate populasi
    population = generate_initial_population(
        depot_indices=DEPOT_INDICES,
        spklu_indices=SPKLU_INDICES,
        customer_indices=CUSTOMER_INDICES,
        vehicle_capacity=VEHICLE_CAPACITY,
        pop_size=POP_SIZE,
        use_spklu=True
    )
    
    # Tampilkan hasil
    print("=" * 60)
    print("POPULASI AWAL")
    print("=" * 60)
    print(f"Jumlah Chromosome: {len(population)}\n")
    
    for i, chromosome in enumerate(population):
        print(f"Chromosome {i+1}:")
        for j, route in enumerate(chromosome):
            route_str = " -> ".join(str(node) for node in route)
            print(f"  Route {j+1}: {route_str}")
        print()