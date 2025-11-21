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
    """Bangkitkan satu kromosom awal dengan format: ['D1', 'C1', 'C2', '|', 'D1', 'C3', 'C4', ...]"""
    depot = evrp_data['depot']
    customers = evrp_data['customers'][:]
    vehicles = evrp_data['vehicles']
    
    random.shuffle(customers)
    chromosome = []
    
    # Jika hanya satu depot
    if len(depot) == 1:
        depot_node = depot[0]
        customers_per_vehicle = len(customers) // vehicles
        
        for v in range(vehicles):
            chromosome.append(f'D{depot_node}')
            
            # Assign customer ke vehicle ini
            start_idx = v * customers_per_vehicle
            if v == vehicles - 1:
                # Vehicle terakhir dapat sisa customer
                end_idx = len(customers)
            else:
                end_idx = (v + 1) * customers_per_vehicle
            
            route_customers = customers[start_idx:end_idx]
            for c in route_customers:
                chromosome.append(f'C{c}')
            
            chromosome.append(f'D{depot_node}')
            
            # Tambah separator kecuali untuk vehicle terakhir
            if v < vehicles - 1:
                chromosome.append('|')
    
    # Jika multi-depot
    else:
        customers_per_vehicle = len(customers) // vehicles
        depot_assignment = []
        
        # Assign depot ke setiap vehicle secara round-robin
        for v in range(vehicles):
            depot_assignment.append(depot[v % len(depot)])
        
        for v in range(vehicles):
            depot_node = depot_assignment[v]
            chromosome.append(f'D{depot_node}')
            
            # Assign customer ke vehicle ini
            start_idx = v * customers_per_vehicle
            if v == vehicles - 1:
                end_idx = len(customers)
            else:
                end_idx = (v + 1) * customers_per_vehicle
            
            route_customers = customers[start_idx:end_idx]
            for c in route_customers:
                chromosome.append(f'C{c}')
            
            chromosome.append(f'D{depot_node}')
            
            # Tambah separator kecuali untuk vehicle terakhir
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
