# file: repair.py
import random

def find_nearest_reachable_station_fast(current_node, station_ids, dist_matrix, current_battery, consumption_rate):
    """
    Mencari station terdekat menggunakan lookup table (dist_matrix).
    O(N) lookup tanpa perhitungan sqrt.
    """
    best_station = None
    min_dist = float('inf')

    for s_id in station_ids:
        # Ambil jarak langsung dari matriks (sangat cepat)
        dist = dist_matrix[current_node][s_id]
        energy_needed = dist * consumption_rate
        
        if current_battery >= energy_needed:
            if dist < min_dist:
                min_dist = dist
                best_station = s_id
                
    return best_station

def calculate_energy_to_next_stop(route, current_idx, dist_matrix, consumption_rate):
    """Hitung energi yang dibutuhkan sampai ketemu charger/depot berikutnya."""
    energy = 0.0
    for i in range(current_idx, len(route) - 1):
        u, v = route[i], route[i+1]
        energy += dist_matrix[u][v] * consumption_rate
        if v.startswith('D') or v.startswith('S'):
            break
    return energy

def repair_chromosome(chromosome, dist_matrix, station_ids, battery_capacity, consumption_rate=1.0):
    """
    Smart Repair dengan Partial Charging & Matrix Lookup.
    """
    # 1. Parsing Routes
    routes = []
    current_route = []
    for gene in chromosome:
        if gene == '|':
            if current_route: routes.append(current_route)
            current_route = []
        else:
            current_route.append(gene)
    if current_route: routes.append(current_route)

    repaired_chromosome = []

    # 2. Logic Perbaikan
    for route in routes:
        if not route: continue
        
        new_route = []
        current_node = route[0]
        new_route.append(current_node)
        
        current_battery = battery_capacity 
        
        i = 0
        while i < len(route) - 1:
            next_node = route[i+1]
            
            # Lookup jarak dari Matrix
            dist = dist_matrix[current_node][next_node]
            energy_needed = dist * consumption_rate
            
            # --- Partial Charging Logic ---
            if current_node.startswith('D') or current_node.startswith('S'):
                energy_required = calculate_energy_to_next_stop(route, i, dist_matrix, consumption_rate)
                # Charge secukupnya (safety margin dikit bisa ditambah kalau mau)
                current_battery = min(battery_capacity, max(current_battery, energy_required))
            
            # --- Cek Perjalanan ---
            if current_battery >= energy_needed:
                current_battery -= energy_needed
                new_route.append(next_node)
                current_node = next_node
                i += 1
            else:
                # Baterai kurang, cari station terdekat via Matrix
                station_id = find_nearest_reachable_station_fast(
                    current_node, station_ids, dist_matrix, current_battery, consumption_rate
                )
                
                if station_id:
                    dist_to_station = dist_matrix[current_node][station_id]
                    current_battery -= (dist_to_station * consumption_rate)
                    new_route.append(station_id)
                    current_node = station_id
                    # Loop ulang dari station ini (i tidak bertambah)
                else:
                    # Dead end, paksa jalan (biar kena penalty di fitness)
                    new_route.append(next_node)
                    current_battery = 0
                    current_node = next_node
                    i += 1

        repaired_chromosome.extend(new_route)
        repaired_chromosome.append('|')

    if repaired_chromosome and repaired_chromosome[-1] == '|':
        repaired_chromosome.pop()

    return repaired_chromosome