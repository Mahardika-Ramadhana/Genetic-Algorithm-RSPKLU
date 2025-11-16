import random

def apply_mutation(chromosome, depot_locations, customer_locations, mutation_probability=0.1, beta=0.2):
    """
    Fungsi memilih antara inter-depot atau intra-depot
    parameter:
        - mutation_probability: probabilitas mutasi terjadi
        - beta: parameter batas untuk menentukan border customer
    """

    if random.random() > mutation_probability:
        return chromosome
    
    border_customers = find_border_customers(chromosome, depot_locations, customer_locations, beta)
    
    if border_customers and random.random() < 0.7:
        print("  [MUTASI] Melakukan Inter-Depot Mutation")
        return inter_depot_mutation(chromosome, border_customers, depot_locations)
    else:
        print("  [MUTASI] Melakukan Intra-Depot Mutation")
        return intra_depot_mutation(chromosome)

def find_border_customers(chromosome, depot_locations, customer_locations, beta):
    """
    Temukan semua border customers dalam kromosom yang feasible untuk inter-depot mutation
    Sesuai paper: menggunakan formula (d_ax + d_ay) / Σ d_al ≥ r
    """
    border_list = []
    routes = extract_routes(chromosome)
    
    for route in routes:
        for customer in route['customers']:
            if is_border_customer(customer, depot_locations, customer_locations, beta):
                candidate_depots = get_candidate_depots(customer, depot_locations, customer_locations, beta)
                if route['depot'] in candidate_depots:
                    candidate_depots.remove(route['depot'])
                
                if candidate_depots:
                    border_list.append({
                        'customer': customer,
                        'current_depot': route['depot'],
                        'candidate_depots': candidate_depots,
                        'current_route': route
                    })
    
    return border_list

def inter_depot_mutation(chromosome, border_customers, depot_locations):
    """
    Melakukan inter-depot mutation pada kromosom
    Hanya untuk border customers yang sudah teridentifikasi
    """
    if not border_customers:
        return chromosome
    
    selected = random.choice(border_customers)
    customer = selected['customer']
    candidate_depots = selected['candidate_depots']
    
    if not candidate_depots:
        return chromosome
    
    # Pilih depot tujuan secara random dari candidate depots
    new_depot = random.choice(candidate_depots)
    
    print(f"  [INTER-DEPOT] Memindahkan {customer} dari {selected['current_depot']} ke {new_depot}")
    
    # Lakukan reassignment customer ke depot barucls
    new_chromosome = reassign_customer_to_depot(chromosome, customer, selected['current_depot'], new_depot)
    
    return new_chromosome

def intra_depot_mutation(chromosome):
    """
    Melakukan intra-depot mutation (dalam depot yang sama)
    Beberapa tipe mutasi yang mungkin: swap, inversion, insertion
    """
    routes = extract_routes(chromosome)
    
    # Filter route yang memiliki minimal 2 customers
    valid_routes = [route for route in routes if len(route['customers']) >= 2]
    
    if not valid_routes:
        return chromosome  # Tidak ada route yang bisa dimutasi
    
    # Pilih random route untuk dimutasi
    selected_route = random.choice(valid_routes)
    customers = selected_route['customers']
    
    # Pilih tipe mutasi secara random
    mutation_type = random.choice(['swap', 'inversion', 'insertion'])
    
    if mutation_type == 'swap' and len(customers) >= 2:
        # Swap mutation - tukar dua posisi random
        pos1, pos2 = random.sample(range(len(customers)), 2)
        customers[pos1], customers[pos2] = customers[pos2], customers[pos1]
        print(f"  [INTRA-DEPOT] Swap {customers[pos2]} dan {customers[pos1]} dalam {selected_route['depot']}")
        
    elif mutation_type == 'inversion' and len(customers) >= 2:
        # Inversion mutation - balik urutan segmen
        start, end = sorted(random.sample(range(len(customers)), 2))
        customers[start:end+1] = reversed(customers[start:end+1])
        print(f"  [INTRA-DEPOT] Inversion posisi {start}-{end} dalam {selected_route['depot']}")
        
    elif mutation_type == 'insertion' and len(customers) >= 2:
        # Insertion mutation - pindah customer ke posisi lain
        if len(customers) >= 2:
            from_pos = random.randint(0, len(customers)-1)
            to_pos = random.randint(0, len(customers)-1)
            while to_pos == from_pos:
                to_pos = random.randint(0, len(customers)-1)
            
            customer_moved = customers.pop(from_pos)
            customers.insert(to_pos, customer_moved)
            print(f"  [INTRA-DEPOT] Insert {customer_moved} dari pos {from_pos} ke {to_pos} dalam {selected_route['depot']}")
    
    # Update full_route
    selected_route['full_route'] = [selected_route['depot']] + customers + [selected_route['depot']]
    
    # Rebuild chromosome dari routes yang sudah dimodifikasi
    new_chromosome = rebuild_chromosome_from_routes(routes)
    
    return new_chromosome

# ===== HELPER FUNCTIONS =====

def extract_routes(chromosome):
    """
    Mengekstrak rute dari representasi kromosom dengan benar
    """
    routes = []
    current_route = []
    
    for gene in chromosome:
        if gene == '|':
            if current_route:
                # Route harus mulai dan berakhir dengan depot yang sama
                if len(current_route) >= 2 and current_route[0].startswith('D') and current_route[-1].startswith('D'):
                    routes.append({
                        'depot': current_route[0],
                        'customers': current_route[1:-1],
                        'full_route': current_route.copy()
                    })
                current_route = []
        else:
            current_route.append(gene)
    
    # Handle last route
    if current_route and len(current_route) >= 2 and current_route[0].startswith('D') and current_route[-1].startswith('D'):
        routes.append({
            'depot': current_route[0],
            'customers': current_route[1:-1],
            'full_route': current_route.copy()
        })
    
    return routes

def rebuild_chromosome_from_routes(routes):
    """
    Membangun kromosom dari list routes dengan benar
    """
    chromosome = []
    for i, route in enumerate(routes):
        # Tambahkan full route
        chromosome.extend(route['full_route'])
        
        # Tambahkan pembatas kecuali untuk route terakhir
        if i < len(routes) - 1:
            chromosome.append('|')
    
    return chromosome

def is_border_customer(customer, depot_locations, customer_locations, beta):
    """
    Menentukan apakah customer adalah border customer berdasarkan formula di paper
    Formula dari paper: (d_ax + d_ay) / Σ d_al ≥ r
    Dimana: 
      d_ax = jarak ke depot terdekat
      d_ay = jarak ke depot kedua terdekat  
      Σ d_al = total jarak ke semua depot
      r = random threshold antara 0-1
    """
    if customer not in customer_locations:
        return False
    
    customer_loc = customer_locations[customer]
    
    # Hitung jarak ke semua depot
    distances = {}
    for depot_id, depot_loc in depot_locations.items():
        dist = euclidean_distance(customer_loc, depot_loc)
        distances[depot_id] = dist
    
    if len(distances) < 2:
        return False  # Perlu minimal 2 depot untuk jadi border customer
    
    # Urutkan berdasarkan jarak
    sorted_depots = sorted(distances.items(), key=lambda x: x[1])
    
    # Depot terdekat dan kedua terdekat
    nearest_depot, nearest_dist = sorted_depots[0]
    second_depot, second_dist = sorted_depots[1]
    
    # Total jarak ke semua depot
    total_distance = sum(distances.values())
    
    # Formula dari paper: (d_ax + d_ay) / Σ d_al ≥ r
    r = 0.3  # Threshold, bisa disesuaikan
    ratio = (nearest_dist + second_dist) / total_distance
    
    # Juga gunakan formula batas: dist(x_i - d_i) - near ≤ β
    border_condition = (second_dist - nearest_dist) <= beta
    
    return ratio >= r and border_condition

def get_candidate_depots(customer, depot_locations, customer_locations, beta):
    """
    Mendapatkan candidate depots untuk inter-depot mutation
    Depot yang memenuhi kriteria border dan feasible
    """
    if customer not in customer_locations:
        return []
    
    customer_loc = customer_locations[customer]
    
    # Hitung jarak ke semua depot
    distances = {}
    for depot_id, depot_loc in depot_locations.items():
        dist = euclidean_distance(customer_loc, depot_loc)
        distances[depot_id] = dist
    
    # Urutkan berdasarkan jarak
    sorted_depots = sorted(distances.items(), key=lambda x: x[1])
    nearest_depot, nearest_dist = sorted_depots[0]
    
    # Ambil depot-depot yang memenuhi kriteria border
    candidate_depots = []
    for depot_id, dist in sorted_depots[1:]:  # Skip depot terdekat
        if dist - nearest_dist <= beta:
            candidate_depots.append(depot_id)
    
    return candidate_depots

def reassign_customer_to_depot(chromosome, customer, old_depot, new_depot):
    """
    Reassign customer dari depot lama ke depot baru
    """
    routes = extract_routes(chromosome)
    
    # 1. Hapus customer dari route lama
    for route in routes:
        if route['depot'] == old_depot and customer in route['customers']:
            route['customers'].remove(customer)
            # Update full_route
            if route['customers']:  # Jika masih ada customers, update route
                route['full_route'] = [route['depot']] + route['customers'] + [route['depot']]
            break
    
    # 2. Hapus route yang kosong
    routes = [route for route in routes if route['customers']]
    
    # 3. Tambahkan customer ke route depot baru
    target_route = None
    for route in routes:
        if route['depot'] == new_depot:
            target_route = route
            break
    
    if target_route:
        # Insert customer di posisi random dalam route yang ada
        if target_route['customers']:
            insert_pos = random.randint(0, len(target_route['customers']))
            target_route['customers'].insert(insert_pos, customer)
        else:
            target_route['customers'].append(customer)
        
        # Update full_route
        target_route['full_route'] = [target_route['depot']] + target_route['customers'] + [target_route['depot']]
    else:
        # Buat route baru untuk depot ini
        new_route = {
            'depot': new_depot,
            'customers': [customer],
            'full_route': [new_depot, customer, new_depot]
        }
        routes.append(new_route)
    
    # Rebuild chromosome
    new_chromosome = rebuild_chromosome_from_routes(routes)
    
    return new_chromosome

def euclidean_distance(coord1, coord2):
    """
    Menghitung Euclidean distance antara dua koordinat
    """
    return ((coord1[0] - coord2[0])**2 + (coord1[1] - coord2[1])**2)**0.5

# ===== CONTOH PENGGUNAAN =====

if __name__ == "__main__":
    # Contoh data dengan depot yang lebih berdekatan untuk testing border customers
    depot_locations = {
        'D1': (23.808247, 90.408963),
        'D2': (23.807329, 90.409563),  # Depot berdekatan untuk testing border
        'D3': (23.833546, 90.433262)   # Depot agak jauh
    }
    
    customer_locations = {
        'C1': (23.808000, 90.409000),  # Di antara D1 dan D2 (border customer)
        'C2': (23.807500, 90.409200),  # Di antara D1 dan D2 (border customer)  
        'C3': (23.831000, 90.432000),  # Dekat D3
        'C4': (23.809000, 90.408000),  # Dekat D1
        'C5': (23.806000, 90.410000)   # Dekat D2
    }
    
    # Contoh kromosom
    contoh_kromosom = ['D1', 'C1', 'C2', 'C4', 'D1', '|', 'D2', 'C5', 'D2', '|', 'D3', 'C3', 'D3']
    
    print("Kromosom awal:", contoh_kromosom)
    print("\n=== MUTASI SESUAI PAPER ===")
    
    for i in range(5):
        print(f"\n--- Percobaan {i+1} ---")
        mutated = apply_mutation(contoh_kromosom, depot_locations, customer_locations, mutation_probability=1.0)
        print(f"Hasil: {mutated}")