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
# Get distance between two nodes
# ---------------------------
def get_distance(a, b, dist):
    if a in dist and b in dist[a]:
        return dist[a][b]
    elif b in dist and a in dist[b]:
        return dist[b][a]
    return float("inf")

# ---------------------------
# Insertion cost in one route
# ---------------------------
def insertion_cost(route, customer, dist):
    if len(route) < 2:
        return 0, 0
    
    best_cost = float("inf")
    best_pos = None
    
    for i in range(len(route) - 1):
        a, b = route[i], route[i+1]
        cost_before = get_distance(a, b, dist)
        cost_after = get_distance(a, customer, dist) + get_distance(customer, b, dist)
        delta = cost_after - cost_before
        
        if delta < best_cost:
            best_cost = delta
            best_pos = i + 1

    return best_cost, best_pos

# ---------------------------
# BCRC crossover using delimiter encoding
# ---------------------------
def bcrc_crossover(chrom1, chrom2, dist):

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
        cost, pos = insertion_cost(route, customer, dist)
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