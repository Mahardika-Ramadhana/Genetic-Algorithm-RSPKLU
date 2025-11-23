def fitness_function(chromosome, distance_matrix=None, node_coords=None,
					 battery_capacity=100, consumption_rate=1.0, charging_rate=1.0,
					 w1=0.6, w2=0.4, stations=None):
	"""
	Compute fitness untuk chromosome dengan simplified charging logic.
	Jika battery tidak cukup, langsung return penalty (tidak coba charging di tengah jalan).
	"""
	total_distance = 0.0
	total_charging_time = 0.0
	invalid_penalty = 1e9

	def extract_id(node_str):
		"""Extract integer ID dari string seperti 'D1', 'C5', 'S3'."""
		try:
			return int(node_str[1:])
		except (ValueError, IndexError):
			return None

	def get_distance(a, b):
		"""Get distance antara node a dan b menggunakan distance_matrix."""
		id_a = extract_id(a) if isinstance(a, str) else a
		id_b = extract_id(b) if isinstance(b, str) else b
		
		if id_a is None or id_b is None:
			return 0.0
		
		if distance_matrix is not None:
			if (id_a, id_b) in distance_matrix:
				return distance_matrix[(id_a, id_b)]
			elif (id_b, id_a) in distance_matrix:
				return distance_matrix[(id_b, id_a)]
		
		if node_coords is not None:
			if id_a in node_coords and id_b in node_coords:
				ax, ay = node_coords[id_a]
				bx, by = node_coords[id_b]
				return ((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5
		
		return 0.0

	# Parse chromosome menjadi routes
	routes = []
	current_route = []
	for gene in chromosome:
		if gene == '|':
			if current_route:
				routes.append(current_route)
			current_route = []
		else:
			current_route.append(gene)
	
	if current_route:
		routes.append(current_route)

	# Count customers per route (untuk penalty single-customer routes)
	total_penalty = 0.0
	for route in routes:
		# Count actual customers (exclude depot and stations)
		customer_count = sum(1 for node in route if isinstance(node, str) and node.startswith('C'))
		# Penalize single-customer routes dengan 0.5 penalty per route
		if customer_count == 1:
			total_penalty += 0.5

	# Evaluasi setiap route
	for route in routes:
		if len(route) < 2:
			continue
		
		battery = battery_capacity
		
		# Traverse route sederhana: jika battery habis, return penalty
		for i in range(len(route) - 1):
			current_node = route[i]
			next_node = route[i + 1]
			
			# Skip jika station (tidak consume energy)
			if isinstance(next_node, str) and next_node.startswith('S'):
				# Charging station - full charge battery
				battery = battery_capacity
				continue
			
			dist = get_distance(current_node, next_node)
			energy_needed = dist * consumption_rate
			total_distance += dist
			
			# Cek battery cukup
			if battery < energy_needed:
				# Tidak cukup battery, return penalty
				return invalid_penalty
			
			battery -= energy_needed
	
	# Hitung fitness
	D = total_distance / 100.0
	C = total_charging_time / 100.0
	fitness = w1 * D + w2 * C + total_penalty
	
	return fitness

