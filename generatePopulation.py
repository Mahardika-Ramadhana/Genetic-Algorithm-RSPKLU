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


def calculate_distance(coords, node1, node2):
    """Calculate Euclidean distance between two nodes."""
    x1, y1 = coords[node1]
    x2, y2 = coords[node2]
    return ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5


def find_nearest_station(coords, current_node, stations):
    """Find the nearest charging station to the current node."""
    min_dist = float('inf')
    nearest_station = None
    
    for station in stations:
        dist = calculate_distance(coords, current_node, station)
        if dist < min_dist:
            min_dist = dist
            nearest_station = station
    
    return nearest_station


def generate_initial_chromosome(evrp_data):
    """Bangkitkan satu kromosom awal dengan format: [1, 2, 3, 1, '|', 31, 4, 5, 31, ...]
    dengan mempertimbangkan energy capacity dan menambahkan charging stations jika diperlukan."""
    depot = evrp_data['depot']
    customers = evrp_data['customers'][:]
    vehicles = evrp_data['vehicles']
    energy_capacity = evrp_data['energy_capacity']
    coords = evrp_data['coords']
    stations = evrp_data['stations']
    consumption_rate = 1.0  # Energy consumed per unit distance
    
    random.shuffle(customers)
    chromosome = []
    
    # Multi-depot setup
    customers_per_vehicle = len(customers) // vehicles
    depot_assignment = []
    
    # Assign depot ke setiap vehicle secara round-robin
    for v in range(vehicles):
        depot_assignment.append(depot[v % len(depot)])
    
    for v in range(vehicles):
        depot_node = depot_assignment[v]
        route = [depot_node]
        
        # Assign customer ke vehicle ini
        start_idx = v * customers_per_vehicle
        if v == vehicles - 1:
            end_idx = len(customers)
        else:
            end_idx = (v + 1) * customers_per_vehicle
        
        route_customers = customers[start_idx:end_idx]
        
        # Build route with energy consideration
        current_energy = energy_capacity
        current_node = depot_node
        
        for idx, c in enumerate(route_customers):
            # Calculate distances
            dist_to_customer = calculate_distance(coords, current_node, c)
            energy_to_customer = dist_to_customer * consumption_rate
            
            # Look ahead: what's the minimum energy we'll need AFTER visiting this customer?
            # We need energy to either reach depot or next customer then depot
            if idx < len(route_customers) - 1:
                # Not last customer - need energy to next customer
                next_customer = route_customers[idx + 1]
                dist_customer_to_next = calculate_distance(coords, c, next_customer)
                dist_next_to_depot = calculate_distance(coords, next_customer, depot_node)
                min_energy_reserve = min(
                    calculate_distance(coords, c, depot_node) * consumption_rate,  # direct to depot
                    (dist_customer_to_next + dist_next_to_depot) * consumption_rate  # via next customer
                )
            else:
                # Last customer - just need to reach depot
                min_energy_reserve = calculate_distance(coords, c, depot_node) * consumption_rate
            
            # Total energy needed: go to customer + minimum reserve
            total_energy_needed = energy_to_customer + min_energy_reserve
            
            # Check if we need charging station
            if current_energy < total_energy_needed and stations:
                # Find nearest station and add it
                nearest_station = find_nearest_station(coords, current_node, stations)
                if nearest_station:
                    dist_to_station = calculate_distance(coords, current_node, nearest_station)
                    energy_to_station = dist_to_station * consumption_rate
                    
                    # Make sure we can reach the station
                    if current_energy >= energy_to_station:
                        route.append(nearest_station)
                        current_energy = energy_capacity  # Fully recharge
                        current_node = nearest_station
                        
                        # Recalculate from station to customer
                        dist_to_customer = calculate_distance(coords, current_node, c)
                        energy_to_customer = dist_to_customer * consumption_rate
            
            # Add customer to route
            route.append(c)
            current_energy -= energy_to_customer
            current_node = c
            
            # Check if we need to recharge before going further
            # (might need station even AFTER adding customer)
            if idx < len(route_customers) - 1:
                next_customer = route_customers[idx + 1]
                dist_to_next = calculate_distance(coords, current_node, next_customer)
                energy_to_next = dist_to_next * consumption_rate
                dist_next_to_depot = calculate_distance(coords, next_customer, depot_node)
                energy_next_to_depot = dist_next_to_depot * consumption_rate
                total_energy_for_next = energy_to_next + energy_next_to_depot
                
                if current_energy < total_energy_for_next and stations:
                    nearest_station = find_nearest_station(coords, current_node, stations)
                    if nearest_station:
                        dist_to_station = calculate_distance(coords, current_node, nearest_station)
                        energy_to_station = dist_to_station * consumption_rate
                        
                        if current_energy >= energy_to_station:
                            route.append(nearest_station)
                            current_energy = energy_capacity
                            current_node = nearest_station
        
        # Check if we can return to depot, if not add station
        dist_to_depot = calculate_distance(coords, current_node, depot_node)
        energy_to_depot = dist_to_depot * consumption_rate
        
        if current_energy < energy_to_depot and stations:
            nearest_station = find_nearest_station(coords, current_node, stations)
            if nearest_station:
                route.append(nearest_station)
                current_energy = energy_capacity
        
        # Return to depot
        route.append(depot_node)
        
        # Convert route to chromosome format (integers only)
        for node in route:
            chromosome.append(node)
        
        # Add separator except for last vehicle
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
    return ' '.join(str(gene) for gene in chromosome)


if __name__ == "__main__":
    # Parse file E-n32-k6-s7-edited.evrp
    filepath = "data/E-n32-k6-s7-edited.evrp"
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
