"""
crossover.py

Crossover operators untuk EVRP genetic algorithm.
Implements BCRC (Best Cost Route Crossover) dan route-based crossover.

Format chromosome: list dengan delimiter '|' untuk route separator
  ['D1', 'C1', 'C2', 'C3', 'S1', 'D2', '|', 'D2', 'C4', 'C5', 'D2']
"""
import random
import copy


# ---------------------------
# Helper: split chromosome by '|'
# ---------------------------
def split_routes(chrom):
    """Split chromosome list into list of routes using '|' delimiter."""
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
    """Join list of routes back into chromosome with '|' delimiter."""
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
    """Remove a specific customer from all routes."""
    new_routes = []
    for r in routes:
        new_routes.append([x for x in r if x != customer])
    return new_routes


# ---------------------------
# Get distance between two nodes
# ---------------------------
def get_distance(a, b, dist_dict):
    """Get distance between two nodes from distance dictionary."""
    if a in dist_dict and b in dist_dict[a]:
        return dist_dict[a][b]
    elif b in dist_dict and a in dist_dict[b]:
        return dist_dict[b][a]
    return float("inf")


# ---------------------------
# Insertion cost in one route
# ---------------------------
def insertion_cost(route, customer, dist_dict):
    """Calculate best insertion cost for customer in route.
    
    Returns:
        (best_cost, best_position): cost increase and insertion position
    """
    if len(route) < 2:
        return 0, 0
    
    best_cost = float("inf")
    best_pos = None
    
    for i in range(len(route) - 1):
        a, b = route[i], route[i+1]
        cost_before = get_distance(a, b, dist_dict)
        cost_after = get_distance(a, customer, dist_dict) + get_distance(customer, b, dist_dict)
        delta = cost_after - cost_before
        
        if delta < best_cost:
            best_cost = delta
            best_pos = i + 1

    return best_cost, best_pos


# ---------------------------
# BCRC crossover using delimiter encoding
# ---------------------------
def bcrc_crossover(chrom1, chrom2, dist_dict):
    """
    Partially Mapped Crossover (PMX) untuk EVRP chromosomes.
    
    Selects random customer dari parent1, removes dari parent2,
    kemudian insert di posisi dengan best insertion cost.
    
    Args:
        chrom1, chrom2: list chromosome dengan '|' delimiter
        dist_dict: dictionary of distances between nodes
    
    Returns:
        child: offspring chromosome
    """
    p1 = copy.deepcopy(chrom1)
    p2 = copy.deepcopy(chrom2)

    # Convert encoding → routes
    routes1 = split_routes(p1)
    routes2 = split_routes(p2)

    # 1. Pick random customer (only C*)
    all_customers = [x for r in routes1 for x in r if x.startswith("C")]
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
        cost, pos = insertion_cost(route, customer, dist_dict)
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


def crossover_route_based(parent1, parent2):
    """
    Route-based crossover: Tukar entire routes antara dua parent.
    Lebih simple dan natural untuk EVRP.
    
    Args:
        parent1, parent2: string chromosome dengan '|' separator
    
    Returns:
        (child1, child2): two offspring chromosomes
    """
    # Split by route separator '|'
    if isinstance(parent1, str):
        routes1 = parent1.split(' | ')
    else:
        p1_str = ' '.join(str(x) for x in parent1)
        routes1 = p1_str.split(' | ')
    
    if isinstance(parent2, str):
        routes2 = parent2.split(' | ')
    else:
        p2_str = ' '.join(str(x) for x in parent2)
        routes2 = p2_str.split(' | ')
    
    if len(routes1) <= 1 or len(routes2) <= 1:
        return parent1, parent2
    
    # Pilih random crossover point antara routes
    max_point = min(len(routes1), len(routes2)) - 1
    if max_point < 2:
        return parent1, parent2
    
    point = random.randint(1, max_point - 1)
    
    # Create offspring dengan menukar routes
    child1_routes = routes1[:point] + routes2[point:]
    child2_routes = routes2[:point] + routes1[point:]
    
    child1 = ' | '.join(child1_routes)
    child2 = ' | '.join(child2_routes)
    
    return child1, child2


def apply_crossover(parent1, parent2, crossover_type='route_based', distance_dict=None):
    """
    Apply crossover operation dengan chosen strategy.
    
    Args:
        parent1, parent2: chromosome (string or list format)
        crossover_type: 'route_based' atau 'bcrc'
        distance_dict: for BCRC crossover, dictionary of distances
    
    Returns:
        (child1, child2): two offspring (in same format as input)
    """
    # Detect input format
    input_is_list = isinstance(parent1, list)
    
    # Convert to list if string
    if isinstance(parent1, str):
        parent1 = parent1.split(' ')
    if isinstance(parent2, str):
        parent2 = parent2.split(' ')
    
    if crossover_type == 'bcrc' and distance_dict:
        child1 = bcrc_crossover(parent1, parent2, distance_dict)
        child2 = bcrc_crossover(parent2, parent1, distance_dict)
    else:  # default: route_based
        # For route-based crossover with list format
        routes1 = split_routes(parent1)
        routes2 = split_routes(parent2)
        
        if len(routes1) <= 1 or len(routes2) <= 1:
            child1, child2 = parent1, parent2
        else:
            # Pilih random crossover point antara routes
            max_point = min(len(routes1), len(routes2)) - 1
            if max_point < 2:
                child1, child2 = parent1, parent2
            else:
                point = random.randint(1, max_point - 1)
                
                # Create offspring dengan menukar routes
                child1_routes = routes1[:point] + routes2[point:]
                child2_routes = routes2[:point] + routes1[point:]
                
                child1 = join_routes(child1_routes)
                child2 = join_routes(child2_routes)
    
    # Convert back to string if input was string
    if not input_is_list:
        child1 = ' '.join(str(x) for x in child1)
        child2 = ' '.join(str(x) for x in child2)
    
    return child1, child2


if __name__ == "__main__":
    # Test crossover dengan contoh dari notebook
    dist = {
        "D1": {"C1":2,"C2":3,"C3":4,"S1":5,"D2":10},
        "C1": {"C2":1,"C3":4,"S1":2,"D2":5},
        "C2": {"C3":2,"S1":3,"D2":6},
        "C3": {"S1":1,"D2":7},
        "S1": {"D2":2},
        "D2": {"C4":3,"C5":4},
        "C4": {"C5":1,"D2":3},
        "C5": {"D2":2}
    }

    p1 = ["D1","C1","C2","C3","S1","D2","|","D2","C4","C5","D2"]
    p2 = ["D1","C2","C4","S1","D2","|","D2","C1","C3","C5","D2"]

    print("Testing BCRC Crossover:")
    child = bcrc_crossover(p1, p2, dist)
    print(f"  Parent 1: {p1}")
    print(f"  Parent 2: {p2}")
    print(f"  Child:    {child}")
    print()
    
    # Test route-based crossover
    p1_str = "D1 C1 C2 C3 S1 D2 | D2 C4 C5 D2"
    p2_str = "D1 C2 C4 S1 D2 | D2 C1 C3 C5 D2"
    
    print("Testing Route-Based Crossover:")
    c1, c2 = crossover_route_based(p1_str, p2_str)
    print(f"  Parent 1: {p1_str}")
    print(f"  Parent 2: {p2_str}")
    print(f"  Child 1:  {c1}")
    print(f"  Child 2:  {c2}")
