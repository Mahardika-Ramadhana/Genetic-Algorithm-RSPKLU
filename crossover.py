import random
import copy

# ---------------------------
# Helper: split chromosome by '|'
# ---------------------------
def split_routes(chrom):
    routes = []
    cur = []
    for x in chrom:
        if x == "|":
            routes.append(cur)
            cur = []
        else:
            cur.append(x)
    routes.append(cur)
    return routes

# ---------------------------
# Helper: join routes back to encoding
# ---------------------------
def join_routes(routes):
    chrom = []
    for i, r in enumerate(routes):
        if i > 0:
            chrom.append("|")
        chrom.extend(r)
    return chrom

# ---------------------------
# Remove customer from all routes
# ---------------------------
def remove_customer_routes(routes, customer):
    new_routes = []
    for r in routes:
        new_routes.append([x for x in r if x != customer])
    return new_routes

# ---------------------------
# Check if node is a customer (not depot or station)
# ---------------------------
def is_customer(node, evrp_data):
    """Check if node is a customer (not depot or station)"""
    if isinstance(node, str):
        return False  # separators
    return node in evrp_data['customers']

# ---------------------------
# Get distance between two nodes
# ---------------------------
def get_distance(a, b, distance_matrix):
    """Get distance using 0-indexed distance matrix (nodes are 1-indexed)"""
    try:
        return distance_matrix[a-1][b-1]
    except (IndexError, TypeError):
        return float("inf")

# ---------------------------
# Insertion cost in one route
# ---------------------------
def insertion_cost(route, customer, distance_matrix):
    if len(route) < 2:
        return 0, 0
    
    best_cost = float("inf")
    best_pos = None
    
    for i in range(len(route) - 1):
        a, b = route[i], route[i+1]
        cost_before = get_distance(a, b, distance_matrix)
        cost_after = get_distance(a, customer, distance_matrix) + get_distance(customer, b, distance_matrix)
        delta = cost_after - cost_before
        
        if delta < best_cost:
            best_cost = delta
            best_pos = i + 1

    return best_cost, best_pos

# ---------------------------
# BCRC crossover using delimiter encoding with integer nodes
# ---------------------------
def bcrc_crossover(chrom1, chrom2, distance_matrix, evrp_data):
    """
    BCRC crossover for EVRP with integer node IDs
    
    Parameters:
    - chrom1, chrom2: chromosomes with integer nodes and '|' separators
    - distance_matrix: 2D list of distances (0-indexed internally)
    - evrp_data: dict with 'customers', 'depot', 'stations' keys
    """
    p1 = copy.deepcopy(chrom1)
    p2 = copy.deepcopy(chrom2)

    # Convert encoding → routes
    routes1 = split_routes(p1)
    routes2 = split_routes(p2)

    # 1. Pick random customer (only customers, not depot/station)
    all_customers = [x for r in routes1 for x in r if is_customer(x, evrp_data)]
    if not all_customers:
        return chrom2
    
    customer = random.choice(all_customers)

    # 2. Remove customer from parent2 routes
    child_routes = remove_customer_routes(routes2, customer)

    # 3. Find best insertion in all routes
    best_global_cost = float("inf")
    best_route_idx = None
    best_insert_pos = None

    for idx, route in enumerate(child_routes):
        if len(route) < 2:
            continue
        cost, pos = insertion_cost(route, customer, distance_matrix)
        if cost < best_global_cost:
            best_global_cost = cost
            best_route_idx = idx
            best_insert_pos = pos

    # 4. Insert customer
    if best_route_idx is not None:
        child_routes[best_route_idx].insert(best_insert_pos, customer)
    else:
        # If no valid position found, add to first non-empty route
        for idx, route in enumerate(child_routes):
            if len(route) >= 2:
                child_routes[idx].insert(1, customer)
                break

    # 5. Convert routes → delimiter encoding
    return join_routes(child_routes)


# ---------------------------
# Main crossover function (wrapper)
# ---------------------------
def crossover(parent1, parent2, evrp_data, distance_matrix=None):
    """
    Perform crossover between two parents to create two offspring
    
    Parameters:
    - parent1, parent2: parent chromosomes (list with integer nodes and '|' separators)
    - evrp_data: EVRP data dictionary
    - distance_matrix: optional distance matrix (will be computed if not provided)
    
    Returns:
    - offspring1, offspring2: two new chromosomes
    """
    # Build distance matrix if not provided
    if distance_matrix is None:
        coords = evrp_data['coords']
        n = len(coords)
        distance_matrix = []
        for i in range(1, n+1):
            row = []
            for j in range(1, n+1):
                if i == j:
                    row.append(0.0)
                else:
                    xi, yi = coords[i]
                    xj, yj = coords[j]
                    dist = ((xi - xj) ** 2 + (yi - yj) ** 2) ** 0.5
                    row.append(dist)
            distance_matrix.append(row)
    
    # Apply BCRC crossover in both directions
    offspring1 = bcrc_crossover(parent1, parent2, distance_matrix, evrp_data)
    offspring2 = bcrc_crossover(parent2, parent1, distance_matrix, evrp_data)
    
    return offspring1, offspring2