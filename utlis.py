
def load_data(file_path):
    # import pandas as pd
    # data = pd.read_csv(file_path)
    # return data
    data=[]
    return data

def get_dist(a,b): # euclidean distance
    """Return Euclidean distance between two coordinate tuples.

    Args:
        a (tuple): (x, y)
        b (tuple): (x, y)

    Returns:
        float: Euclidean distance
    """
    try:
        return euclidean_distance(a, b)
    except Exception:
        # Fallback: if inputs are numeric scalars, return absolute difference
        try:
            return abs(a - b)
        except Exception:
            raise

def euclidean_distance(coord1, coord2):
    """Compute Euclidean distance between two 2D coordinates.

    coord1, coord2 should be indexable with at least two elements (x,y).
    """
    import math
    return math.hypot(coord1[0] - coord2[0], coord1[1] - coord2[1])


def calculate_distance_matrix(node_coords):
    """
    Hitung distance matrix untuk semua pasangan node.
    
    Parameters:
    - node_coords: Dict {node_id: (x, y)}
    
    Returns:
    - distance_matrix: Dict {(node_id_1, node_id_2): distance}
    """
    distance_matrix = {}
    nodes = list(node_coords.keys())
    
    for i, node_a in enumerate(nodes):
        for node_b in nodes[i+1:]:
            dist = euclidean_distance(node_coords[node_a], node_coords[node_b])
            distance_matrix[(node_a, node_b)] = dist
            distance_matrix[(node_b, node_a)] = dist  # Symmetric
    
    return distance_matrix
