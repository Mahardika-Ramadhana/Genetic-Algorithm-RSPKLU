import random

def get_elites(population, fitness_scores, elite_size):
    """
    Membantu 'selection': Memilih individu terbaik (elites) dari populasi.
    Berdasarkan skor fitness, di mana nilai yang lebih rendah lebih baik.
    """
    # Pasangkan setiap individu dengan skor fitness-nya
    population_with_fitness = list(zip(population, fitness_scores))
    
    # Urutkan berdasarkan fitness (ascending, karena lebih rendah lebih baik)
    sorted_population = sorted(population_with_fitness, key=lambda x: x[1])
    
    # Ambil 'elite_size' individu terbaik
    elites = [individual for individual, fitness in sorted_population[:elite_size]]
    
    return elites

def run_tournament(population, fitness_scores, tournament_size):
    """
    Membantu 'selection': Menjalankan satu putaran tournament selection.
    Memilih 'tournament_size' individu secara acak dan mengembalikan
    yang terbaik (skor fitness terendah) dari kelompok tersebut.
    """
    # Defensive guards
    n = len(population)
    if n == 0:
        return None
    if len(fitness_scores) != n:
        raise ValueError("population and fitness_scores must have same length")

    # Pilih indeks untuk turnamen. Jika tournament_size > n kita sampling dengan replacement
    if tournament_size <= n:
        tournament_indices = random.sample(range(n), tournament_size)
    else:
        tournament_indices = random.choices(range(n), k=tournament_size)

    # Siapkan variabel untuk melacak pemenang
    best_individual = None
    best_fitness = float('inf')  # mencari nilai minimum

    # Loop melalui peserta turnamen
    for index in tournament_indices:
        individual = population[index]
        fitness = fitness_scores[index]

        # Jika individu ini lebih baik dari pemenang saat ini, jadikan dia pemenang
        if fitness < best_fitness:
            best_fitness = fitness
            best_individual = individual

    return best_individual

# --- FUNGSI UTAMA SELECTION ---
def selection(population, fitness_scores, elite_size, tournament_size):
    """
    Melakukan proses seleksi utama menggabungkan Elitism dan Tournament Selection
    untuk memilih orang tua (parents) untuk generasi berikutnya.
    
    Args:
        population (list): Daftar semua kromosom di populasi saat ini.
        fitness_scores (list): Daftar skor fitness yang sesuai dengan 'population'.
        elite_size (int): Jumlah individu terbaik yang akan lolos (Elitism).
        tournament_size (int): Jumlah individu yang bertarung di setiap turnamen.

    Returns:
        list: Daftar orang tua baru yang terpilih (new_parents).
    """
    # Validate inputs
    if not population:
        return []
    if len(fitness_scores) != len(population):
        raise ValueError("population and fitness_scores must have same length")

    # Clamp elite_size
    elite_size = max(0, min(elite_size, len(population)))

    new_parents = []

    # 1. Elitism
    elites = get_elites(population, fitness_scores, elite_size)
    new_parents.extend(elites)

    # 2. Tournament Selection for remaining slots
    num_to_select = len(population) - elite_size
    for _ in range(num_to_select):
        parent = run_tournament(population, fitness_scores, tournament_size)
        if parent is None:
            # Should not happen because we validated population non-empty, but guard anyway
            continue
        new_parents.append(parent)

    return new_parents

# --- CONTOH PENGGUNAAN ---
if __name__ == "__main__":
    
    # Ini adalah POPULASI TIRUAN (DUMMY)
    DUMMY_POPULATION = [
        ['D1', 'C1', 'S1', 'C2', 'D2'],  # Kromosom 1
        ['D2', 'C3', 'C4', 'D1'],       # Kromosom 2
        ['D1', 'C5', 'D1'],             # Kromosom 3
        ['D2', 'C1', 'C3', 'S1', 'C2', 'C4', 'D2'], # Kromosom 4
        ['D1', 'C4', 'C2', 'S1', 'C1', 'C3', 'D1']  # Kromosom 5
    ]
    
    # Ini adalah SKOR FITNESS TIRUAN (DUMMY)
    # [cite_start](Nilai LEBIH RENDAH = LEBIH BAIK, sesuai problem statement 'minimize' [cite: 34])
    DUMMY_FITNESS_SCORES = [
        150.5,  # Fitness untuk Kromosom 1
        120.2,  # Fitness untuk Kromosom 2 (Terbaik)
        210.0,  # Fitness untuk Kromosom 3
        185.7,  # Fitness untuk Kromosom 4
        135.9   # Fitness untuk Kromosom 5 (Kedua terbaik)
    ]
    
    # Parameter untuk GA
    ELITE_SIZE = 1       # Jumlah individu terbaik yang langsung dipertahankan [cite: 208]
    TOURNAMENT_SIZE = 2  # Jumlah individu yang bersaing di setiap turnamen [cite: 205]

    print("--- POPULASI AWAL & FITNESS ---")
    for i in range(len(DUMMY_POPULATION)):
        print(f"Fitness: {DUMMY_FITNESS_SCORES[i]:.1f} | Kromosom: {DUMMY_POPULATION[i]}")

    # === PANGGIL FUNGSI SELECTION ===
    selected_parents = selection(
        DUMMY_POPULATION, 
        DUMMY_FITNESS_SCORES, 
        ELITE_SIZE, 
        TOURNAMENT_SIZE
    )

    print(f"\n--- ORANG TUA TERPILIH (Ukuran: {len(selected_parents)}) ---")
    print(f"(Menggunakan Elitism: {ELITE_SIZE} & Tournament Size: {TOURNAMENT_SIZE})")
    
    # Tampilkan hasil
    for i, parent in enumerate(selected_parents):
        print(f"Orang Tua {i+1}: {parent}")