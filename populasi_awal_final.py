import random
import math
import csv

# ----- LOAD DATA DARI CSV -----
def load_nodes_from_csv(filename):
    """
    Load data node dari file CSV
    Returns: Dictionary dengan struktur {index: {'x': float, 'y': float, 'demand': int}}
    """
    nodes_data = {}
    with open(filename, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file, delimiter=';')
        for row in reader:
            try:
                index = int(row['index'])
                x = float(row['x'].replace(',', '.'))
                y = float(row['y'].replace(',', '.'))
                demand = int(row['Demand'])
                nodes_data[index] = {'x': x, 'y': y, 'demand': demand}
            except (ValueError, KeyError):
                # Skip baris yang tidak valid atau header kosong
                continue
    return nodes_data

# ----- KONFIGURASI PROBLEM -----
class MDVRPConfig:
    def __init__(self, csv_filename, depot_indices, spklu_indices=None, customer_indices=None, vehicle_capacity=500):
        """
        Inisialisasi konfigurasi MDVRP
        
        Args:
            csv_filename: Path ke file CSV
            depot_indices: List of indices yang dijadikan depot (contoh: [1, 42])
            spklu_indices: List of indices yang dijadikan SPKLU (opsional, contoh: [82, 122])
            customer_indices: List of indices yang dijadikan customer (opsional, jika None maka semua node kecuali depot/SPKLU)
            vehicle_capacity: Kapasitas kendaraan
        """
        self.nodes_data = load_nodes_from_csv(csv_filename)
        self.depot_indices = depot_indices
        self.spklu_indices = spklu_indices if spklu_indices else []
        self.vehicle_capacity = vehicle_capacity
        
        # Identifikasi customer
        if customer_indices is not None:
            # Jika customer_indices dispesifikkan, gunakan itu
            self.customer_indices = [idx for idx in customer_indices if idx in self.nodes_data]
        else:
            # Jika tidak, ambil semua node kecuali depot dan SPKLU
            all_indices = set(self.nodes_data.keys())
            depot_set = set(depot_indices)
            spklu_set = set(self.spklu_indices)
            self.customer_indices = list(all_indices - depot_set - spklu_set)
        
    def get_node_info(self, index):
        """Mendapatkan informasi node berdasarkan index"""
        if index in self.nodes_data:
            node = self.nodes_data[index]
            return node['x'], node['y'], node['demand']
        return None
    
    def get_demand(self, index):
        """Mendapatkan demand dari node (0 jika depot/SPKLU)"""
        if index in self.depot_indices or index in self.spklu_indices:
            return 0
        if index in self.nodes_data:
            return self.nodes_data[index]['demand']
        return 0
    
    def calculate_distance(self, index1, index2):
        """Menghitung jarak Euclidean antara dua node"""
        if index1 not in self.nodes_data or index2 not in self.nodes_data:
            return float('inf')
        
        node1 = self.nodes_data[index1]
        node2 = self.nodes_data[index2]
        
        dx = node1['x'] - node2['x']
        dy = node1['y'] - node2['y']
        
        return math.sqrt(dx**2 + dy**2)

# ----- FUNGSI UTILITY -----
def calculate_route_demand(route, config):
    """Menghitung total demand dari rute"""
    return sum(config.get_demand(index) for index in route)

def calculate_route_distance(route, config):
    """Menghitung total jarak dari rute"""
    total_distance = 0
    for i in range(len(route) - 1):
        total_distance += config.calculate_distance(route[i], route[i+1])
    return total_distance

# ----- FUNGSI GENERATE POPULASI AWAL -----
def generate_initial_population(config, pop_size=10, use_spklu=True):
    """
    Generate populasi awal untuk Algoritma Genetika pada MDVRP.
    
    Chromosome representation:
    - Setiap chromosome adalah list of routes
    - Setiap route: [Depot_Awal] + [Customers] + [SPKLU (opsional)] + [Depot_Akhir]
    - Customers didistribusikan ke multiple routes berdasarkan kapasitas
    
    Args:
        config: MDVRPConfig object
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
        remaining_customers = config.customer_indices.copy()
        random.shuffle(remaining_customers)
        
        # Assign customers ke rute berdasarkan kapasitas
        while remaining_customers:
            # Pilih depot awal dan akhir secara random
            start_depot = random.choice(config.depot_indices)
            end_depot = random.choice(config.depot_indices)
            
            # Bentuk rute dengan memperhatikan kapasitas
            route_customers = []
            current_demand = 0
            
            # Masukkan customers selama tidak melebihi kapasitas
            for customer in remaining_customers[:]:
                customer_demand = config.get_demand(customer)
                if current_demand + customer_demand <= config.vehicle_capacity:
                    route_customers.append(customer)
                    current_demand += customer_demand
            
            # Jika tidak ada customer yang bisa ditambahkan, ambil satu
            if not route_customers and remaining_customers:
                route_customers.append(remaining_customers[0])
            
            if not route_customers:
                break
            
            # Bentuk rute lengkap
            if use_spklu and config.spklu_indices:
                spklu = random.choice(config.spklu_indices)
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


    def generate_initial_population_flat(config, pop_size=10, use_spklu=True):
        """Wrapper: returns delimiter-flat chromosomes by flattening nested routes.

        This preserves the original generator behavior while providing the
        delimiter-flat format used by the GA modules (e.g. ['D1','C1','D1','|',...]).
        """
        from utils import flatten_from_nested

        nested = generate_initial_population(config, pop_size=pop_size, use_spklu=use_spklu)
        flat_pop = []
        for chrom in nested:
            flat_pop.append(flatten_from_nested(chrom))
        return flat_pop

# ----- MAIN -----
if __name__ == "__main__":
    print("=" * 80)
    print("GENERATE POPULASI AWAL - ALGORITMA GENETIKA MDVRP DENGAN CSV")
    print("=" * 80)
    
    # ===== KONFIGURASI INPUT =====
    # Silakan modifikasi sesuai kebutuhan
    CSV_FILE = 'data_koordinat.csv'
    DEPOT_INDICES = [1, 42]  # Indeks node yang dijadikan depot
    SPKLU_INDICES = [82, 122]  # Indeks node yang dijadikan SPKLU (opsional)
    
    # ===== KONFIGURASI CUSTOMER =====
    # Pilihan 1: Custom customer dengan indeks spesifik
    CUSTOMER_INDICES = [2, 3, 4]
    
    # Pilihan 2: Ambil N customer pertama dari dataset (uncommment untuk menggunakan)
    # N_CUSTOMERS = 20
    # all_nodes = load_nodes_from_csv(CSV_FILE)
    # CUSTOMER_INDICES = [idx for idx in sorted(all_nodes.keys()) 
    #                     if idx not in DEPOT_INDICES and idx not in SPKLU_INDICES][:N_CUSTOMERS]
    
    # Pilihan 3: Gunakan semua node sebagai customer kecuali depot dan SPKLU (uncomment untuk menggunakan)
    # CUSTOMER_INDICES = None  # None = otomatis ambil semua kecuali depot/SPKLU
    
    VEHICLE_CAPACITY = 100  # Kapasitas kendaraan
    USE_SPKLU = True  # Apakah menggunakan SPKLU dalam rute
    POP_SIZE = 5  # Ukuran populasi
    
    # Inisialisasi konfigurasi
    config = MDVRPConfig(CSV_FILE, DEPOT_INDICES, SPKLU_INDICES, CUSTOMER_INDICES, VEHICLE_CAPACITY)
    
    # Info data
    total_demand = sum(config.get_demand(c) for c in config.customer_indices)
    min_routes = math.ceil(total_demand / VEHICLE_CAPACITY)
    
    print(f"\n{'INFORMASI DATASET':^80}")
    print("=" * 80)
    print(f"Total Nodes dalam CSV       : {len(config.nodes_data)}")
    print(f"Depot Indices               : {DEPOT_INDICES}")
    print(f"SPKLU Indices               : {SPKLU_INDICES if USE_SPKLU else 'Tidak digunakan'}")
    print(f"Customer Indices            : {config.customer_indices}")
    print(f"Jumlah Customers            : {len(config.customer_indices)}")
    print(f"Total Demand                : {total_demand}")
    print(f"Kapasitas Kendaraan         : {VEHICLE_CAPACITY}")
    print(f"Minimum Routes Diperlukan   : {min_routes}")
    
    # Generate populasi
    print("\n" + "=" * 80)
    print(f"{'HASIL GENERATE POPULASI AWAL':^80}")
    print("=" * 80)
    
    population = generate_initial_population(config, pop_size=POP_SIZE, use_spklu=USE_SPKLU)
    
    print(f"\nJumlah Chromosome yang Berhasil Digenerate: {len(population)}")
    
    # Tampilkan setiap chromosome
    for i, chromosome in enumerate(population):
        print(f"\n{'='*80}")
        print(f"CHROMOSOME {i+1}")
        print(f"{'='*80}")
        print(f"Jumlah Routes: {len(chromosome)}")
        
        total_chromosome_distance = 0
        
        for j, route in enumerate(chromosome):
            demand = calculate_route_demand(route, config)
            distance = calculate_route_distance(route, config)
            utilization = (demand / VEHICLE_CAPACITY) * 100
            total_chromosome_distance += distance
            
            # Format route display
            route_str = " -> ".join(str(idx) for idx in route)
            
            print(f"\n  Route {j+1}:")
            print(f"    Sequence: {route_str}")
            print(f"    Demand  : {demand}/{VEHICLE_CAPACITY} ({utilization:.1f}%)")
            print(f"    Distance: {distance:.2f}")
        
        print(f"\n  Total Distance Chromosome: {total_chromosome_distance:.2f}")
    
    print("\n" + "=" * 80)
    print("SELESAI")
    print("=" * 80)
    
    # Contoh penggunaan dengan konfigurasi berbeda
    print("\n" + "=" * 80)
    print("CONTOH PENGGUNAAN DENGAN KONFIGURASI BERBEDA")
    print("=" * 80)
    print("\nUntuk mengubah konfigurasi, modifikasi variabel berikut:")
    print("  - CSV_FILE: Path ke file CSV")
    print("  - DEPOT_INDICES: List indeks yang menjadi depot")
    print("  - SPKLU_INDICES: List indeks yang menjadi SPKLU")
    print("  - CUSTOMER_INDICES: List indeks yang menjadi customer (atau None untuk semua)")
    print("  - VEHICLE_CAPACITY: Kapasitas kendaraan")
    print("  - USE_SPKLU: True/False untuk menggunakan SPKLU")
    print("  - POP_SIZE: Ukuran populasi yang diinginkan")
    print("\nContoh konfigurasi customer:")
    print("  # Custom 10 customer tertentu")
    print("  CUSTOMER_INDICES = [2, 5, 8, 11, 14, 17, 20, 23, 26, 29]")
    print("\n  # Ambil 50 customer pertama")
    print("  N_CUSTOMERS = 50")
    print("  CUSTOMER_INDICES = [idx for idx in sorted(all_nodes.keys())")
    print("                      if idx not in DEPOT_INDICES][:N_CUSTOMERS]")
    print("\n  # Gunakan semua node sebagai customer (kecuali depot/SPKLU)")
    print("  CUSTOMER_INDICES = None")