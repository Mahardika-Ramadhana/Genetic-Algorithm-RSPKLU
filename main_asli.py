# config:- jumlah kendararn, list depot, capasitas kendaraan, buat init params
# populasi awal, seleksi, crossover, mutasi, fitness function, loop generasi, stop kriteria

config={
    'num_vehicles': 3,
    'depot_list': ['D1', 'D2'],
    'vehicle_capacity': 100,
    # CSV dataset path
    'csv_file': 'data_koordinat.csv',
    # default depot / spklu indices (use actual indices from dataset)
    'depot_indices': [1, 42],
    'spklu_indices': [82, 122],
    # GA params
    'pop_size': 20,
    'generations': 50,
    'elite_size': 2,
    'tournament_size': 3,
    'mutation_prob': 0.2,
    'seed': 42,
}
