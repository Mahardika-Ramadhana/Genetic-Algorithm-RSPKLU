def fitness_function(chromosome, distance_matrix=None, node_coords=None,
					 battery_capacity=100, consumption_rate=1.0, charging_rate=1.0,
					 w1=0.6, w2=0.4):
	"""Compute fitness for a chromosome.

	Parameters
	- chromosome: list of genes with '|' separators between routes
	- distance_matrix: optional dict of pairwise distances
	- node_coords: optional dict {index: (x,y)} if distance_matrix not provided

	Returns: lower is better
	"""
	total_distance = 0.0
	total_charging_time = 0.0
	invalid_penalty = 1e6

	# helper to get distance
	def get_dist(a, b):
		if distance_matrix:
			if (a, b) in distance_matrix:
				return distance_matrix[(a, b)]
			if (b, a) in distance_matrix:
				return distance_matrix[(b, a)]
		if node_coords and a in node_coords and b in node_coords:
			ax, ay = node_coords[a]
			bx, by = node_coords[b]
			return ((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5
		return 0.0

	# Support two chromosome formats:
	# 1) flat list with '|' separators (e.g., ['D1','C1','D1','|','D2','C2','D2'])
	# 2) list of routes where each route is a list of node indices (e.g., [[1,2,3],[4,5,6]])
	routes = []
	if chromosome and isinstance(chromosome[0], (list, tuple)):
		# already a list of routes (nodes may be ints)
		routes = [list(route) for route in chromosome]
		# Simple distance-only simulation (no charging logic for numeric ids)
		for route in routes:
			for i in range(len(route) - 1):
				a, b = route[i], route[i+1]
				dist = get_dist(a, b)
				total_distance += dist
	else:
		# flat representation with '|' separators
		current = []
		for gene in chromosome:
			if gene == '|':
				if current:
					routes.append(current)
					current = []
			else:
				current.append(gene)
		if current:
			routes.append(current)

		for route in routes:
			battery = battery_capacity
			for i in range(len(route) - 1):
				a, b = route[i], route[i+1]
				dist = get_dist(a, b)
				total_distance += dist
				needed_energy = dist * consumption_rate

				# handle charging station (gene contains 'S')
				if isinstance(a, str) and 'S' in a:
					energy_needed_to_next = 0.0
					for j in range(i, len(route) - 1):
						u, v = route[j], route[j+1]
						energy_needed_to_next += get_dist(u, v) * consumption_rate
						if isinstance(v, str) and ('S' in v or 'D' in v):
							break
					required_energy = max(0.0, energy_needed_to_next - battery)
					charge_time = required_energy / charging_rate if charging_rate > 0 else 0.0
					total_charging_time += charge_time
					battery = min(battery + required_energy, battery_capacity)

				if battery < needed_energy:
					return invalid_penalty
				battery -= needed_energy

	D = total_distance / 100.0
	C = total_charging_time / 100.0
	fitness = w1 * D + w2 * C
	return fitness

