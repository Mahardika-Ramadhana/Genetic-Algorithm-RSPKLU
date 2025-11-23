# configuration.py

config = {
    # Path ke file dataset EVRP Anda
    'evrp_file': 'X-n1012-k43-s5-edited.evrp',
    
    # Parameter GA
    'pop_size': 50,          # Ukuran populasi
    'generations': 100,      # Jumlah generasi
    'elite_size': 2,         # Jumlah elit yang dipertahankan
    'tournament_size': 5,    # Ukuran turnamen seleksi
    'mutation_prob': 0.3,    # Probabilitas mutasi
    
    # Bobot Fitness (sesuai fitness.py)
    'w1': 0.6, # Bobot jarak
    'w2': 0.4, # Bobot waktu charging
}