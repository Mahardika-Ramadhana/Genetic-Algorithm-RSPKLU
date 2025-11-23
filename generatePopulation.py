import random
from collections import defaultdict

def parse_evrp_file(filepath):
    """Parse file EVRP dan extract informasi depot, customer, station, dan koordinat."""
    coords = {}
    depot = []
    customers = []
    stations = []
    demands = {}
    vehicles = 0
    capacity = 0
    energy_capacity = 0
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
        
        # Parse header
        for line in lines:
            if line.startswith('VEHICLES:'):
                vehicles = int(line.split(':')[1].strip())
            elif line.startswith('CAPACITY:'):
                capacity = int(line.split(':')[1].strip())
            elif line.startswith('ENERGY_CAPACITY:'):
                energy_capacity = int(line.split(':')[1].strip())
        
        # Parse NODE_COORD_SECTION
        node_section = False
        for line in lines:
            if line.strip() == 'NODE_COORD_SECTION':
                node_section = True
                continue
            if node_section:
                if line.strip() == '' or line.strip() == 'DEMAND_SECTION':
                    node_section = False
                    break
                parts = line.strip().split()
                if len(parts) >= 3:
                    node_id = int(parts[0])
                    x = float(parts[1])
                    y = float(parts[2])
                    coords[node_id] = (x, y)
        
        # Parse DEMAND_SECTION
        demand_section = False
        for line in lines:
            if line.strip() == 'DEMAND_SECTION':
                demand_section = True
                continue
            if demand_section:
                if line.strip() == '' or line.strip() == 'STATIONS_COORD_SECTION':
                    demand_section = False
                    break
                parts = line.strip().split()
                if len(parts) >= 2:
                    node_id = int(parts[0])
                    demand = int(parts[1])
                    demands[node_id] = demand
        
        # Parse DEPOT_SECTION
        depot_section = False
        for line in lines:
            if line.strip() == 'DEPOT_SECTION':
                depot_section = True
                continue
            if depot_section:
                if line.strip() == '-1' or line.strip() == 'EOF':
                    break
                if line.strip().isdigit():
                    depot.append(int(line.strip()))
        
        # Parse STATIONS_COORD_SECTION
        station_section = False
        station_ids = []
        for line in lines:
            if line.strip() == 'STATIONS_COORD_SECTION':
                station_section = True
                continue
            if station_section:
                if line.strip() == '' or line.strip() == 'DEPOT_SECTION':
                    break
                if line.strip().isdigit():
                    station_ids.append(int(line.strip()))
        
        # Customer = node yang bukan depot dan bukan station
        all_nodes = set(coords.keys())
        customer_nodes = all_nodes - set(depot) - set(station_ids)
        customers = sorted(list(customer_nodes))
        stations = sorted(station_ids)
    
    return {
        'coords': coords,
        'depot': sorted(depot),
        'customers': customers,
        'stations': stations,
        'demands': demands,
        'vehicles': vehicles,
        'capacity': capacity,
        'energy_capacity': energy_capacity
    }


def generate_initial_chromosome(evrp_data):
    """
    Bangkitkan satu kromosom awal dengan format: ['D1', 'C1', 'C2', '|', 'D1', 'C3', 'C4', ...]
    PENTING: Setiap vehicle HARUS mendapat AT LEAST 2+ customers untuk menghindari single-customer routes
    Exception: jika total customers < 2*vehicles, maka beberapa vehicle dapat <2 customers
    """
    depot = evrp_data['depot']
    customers = evrp_data['customers'][:]
    vehicles = evrp_data['vehicles']
    stations = evrp_data['stations']
    
    random.shuffle(customers)
    chromosome = []
    
    # Strategy: Distribute customers untuk minimize single-customer routes
    # Target: setiap vehicle dapat minimal 2 customers jika possible
    num_customers = len(customers)
    
    # Calculate how many vehicles actually get customers
    if num_customers >= 2 * vehicles:
        # Cukup customers untuk 2+ per vehicle
        num_vehicles_with_customers = vehicles
        min_customers_per_vehicle = 2
    elif num_customers >= vehicles:
        # Cukup untuk >=1 per vehicle, aim untuk 1-2
        num_vehicles_with_customers = min(vehicles, num_customers)
        min_customers_per_vehicle = 1
    else:
        # Customers lebih sedikit dari vehicles
        num_vehicles_with_customers = num_customers
        min_customers_per_vehicle = 1
    
    # Balanced distribution
    customers_per_vehicle = num_customers // num_vehicles_with_customers if num_vehicles_with_customers > 0 else 0
    remainder = num_customers % num_vehicles_with_customers if num_vehicles_with_customers > 0 else 0
    
    if len(depot) == 1:
        depot_node = depot[0]
        
        vehicle_customers = []
        customer_idx = 0
        
        # Distribute customers
        for v in range(num_vehicles_with_customers):
            count = customers_per_vehicle + (1 if v < remainder else 0)
            vehicle_customers.append(customers[customer_idx:customer_idx + count])
            customer_idx += count
        
        # Vehicles tanpa customers (empty)
        for v in range(num_vehicles_with_customers, vehicles):
            vehicle_customers.append([])
        
        # Build chromosome
        for v in range(vehicles):
            chromosome.append(f'D{depot_node}')
            
            # Add customers untuk vehicle ini
            for c in vehicle_customers[v]:
                chromosome.append(f'C{c}')
                # Add charging station dengan probabilitas 10% per customer (reduced dari 15%)
                if random.random() < 0.10 and stations:
                    random_station = random.choice(stations)
                    chromosome.append(f'S{random_station}')
            
            # Add return ke depot
            chromosome.append(f'D{depot_node}')
            
            # Add separator kecuali vehicle terakhir
            if v < vehicles - 1:
                chromosome.append('|')
    
    # Multi-depot case
    else:
        depot_assignment = []
        for v in range(vehicles):
            depot_assignment.append(depot[v % len(depot)])
        
        vehicle_customers = []
        customer_idx = 0
        
        for v in range(num_vehicles_with_customers):
            count = customers_per_vehicle + (1 if v < remainder else 0)
            vehicle_customers.append(customers[customer_idx:customer_idx + count])
            customer_idx += count
        
        for v in range(num_vehicles_with_customers, vehicles):
            vehicle_customers.append([])
        
        # Build chromosome
        for v in range(vehicles):
            depot_node = depot_assignment[v]
            chromosome.append(f'D{depot_node}')
            
            for c in vehicle_customers[v]:
                chromosome.append(f'C{c}')
                if random.random() < 0.10 and stations:
                    random_station = random.choice(stations)
                    chromosome.append(f'S{random_station}')
            
            chromosome.append(f'D{depot_node}')
            
            if v < vehicles - 1:
                chromosome.append('|')
    
    return chromosome


def generate_initial_population(evrp_data, population_size=10):
    """Bangkitkan populasi awal sejumlah population_size kromosom."""
    population = []
    for _ in range(population_size):
        chromosome = generate_initial_chromosome(evrp_data)
        population.append(chromosome)
    return population


def print_chromosome(chromosome):
    """Cetak kromosom dalam format yang mudah dibaca."""
    return ' '.join(chromosome)


if __name__ == "__main__":
    # Parse file E-n32-k6-s7-edited.evrp
    filepath = "e-cvrp_benchmark_instances-master/E-n32-k6-s7-edited.evrp"
    evrp_data = parse_evrp_file(filepath)
    
    print("=== Data EVRP ===")
    print(f"Depot: {evrp_data['depot']}")
    print(f"Customers: {evrp_data['customers']}")
    print(f"Stations: {evrp_data['stations']}")
    print(f"Total Vehicles: {evrp_data['vehicles']}")
    print(f"Capacity: {evrp_data['capacity']}")
    print(f"Energy Capacity: {evrp_data['energy_capacity']}")
    print()
    
    # Bangkitkan populasi awal
    print("=== Populasi Awal ===")
    population = generate_initial_population(evrp_data, population_size=5)
    for idx, chromosome in enumerate(population):
        print(f"Kromosom {idx + 1}: {print_chromosome(chromosome)}")
