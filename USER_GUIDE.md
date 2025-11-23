# User Guide & Recommended Enhancements

## Quick Start

### Run the GA
```bash
cd c:\Project\Genetic-Algorithm-RSPKLU
python main.py
```

### Output Interpretation
```
[GEN 1/50]
[STEP 1] Evaluasi fitness...
  Min Fitness: 6.8392, Avg Fitness: 6.9521
  
This means:
- Generation 1 of 50
- Best fitness in population: 6.8392
- Average fitness across population: 6.9521
(Lower is better - minimizing distance & charging time)
```

### Understanding Results
```
Best Fitness: 6.1441
Infeasible Solutions Eliminated: 1

Best Solution shows:
- 6 routes (one per vehicle)
- All 22 customers served
- Reasonable distribution of customers per route
- Fitness = w1*(distance/100) + w2*(charging_time/100) + penalties
```

---

## Current Parameter Configuration

### File: `main.py`
```python
# GA Parameters
population_size = 20           # Number of chromosomes per generation
generations = 50               # Total generations to run
elite_size = 5                 # Best solutions always kept
tournament_size = 5            # Tournament selection size
mutation_probability = 0.1     # 10% chance per chromosome to mutate
crossover_probability = 0.8    # 80% crossover application rate

# Problem Parameters (Vehicle)
battery_capacity = 300         # Energy units (tuned for feasibility)
consumption_rate = 0.5         # Energy consumed per distance unit
charging_rate = 1.0            # Energy restored per charging station visit

# Fitness Weights
w1 = 0.6                       # Distance weight
w2 = 0.4                       # Charging time weight
```

### Data File Used
```
E-n32-k6-s7-edited.evrp
- 22 customers to serve
- 6 vehicles available
- 7 charging stations
- 3 depots (D1, D31, D32)
- Multi-depot electric vehicle routing problem
```

---

## Optimization Techniques Used

### 1. **Elitism + Tournament Selection**
```
- Keep top 5 best solutions each generation (elitism)
- Select parents via tournament (random 5, pick best)
- Ensures best solutions never lost
```

### 2. **Multi-Point Crossover**
```
- BCRC (Best Cost Route Crossover)
- Inherits route structures from parents
- Preserves good route patterns
```

### 3. **Dual Mutation Operators**
```
- Inter-Depot: Move customer between different depots
- Intra-Depot: Reorder customers within same route
```

### 4. **Infeasible Solution Handling**
```
- Detect: If fitness > 1e8, chromosome is infeasible
- Replace: Generate new random chromosome
- Track: Count total infeasible eliminations
```

### 5. **Single-Customer Route Penalty**
```
- Fitness penalty: -0.5 per single-customer route
- Encourages consolidation
- Result: Balanced customer distribution
```

---

## Performance Comparison: Different Problem Instances

To test with different EVRP files:

```python
# In main.py, line: 
evrp_file = 'data/E-n32-k6-s7-edited.evrp'

# Change to:
evrp_file = 'data/X-n469-k26-s10.evrp'  # Larger instance
```

**Expected Scaling:**
| Problem | Customers | Vehicles | Expected Fitness | Generations Needed |
|---------|-----------|----------|------------------|--------------------|
| E-n32-k6-s7 | 22 | 6 | ~6.1 | 50 |
| E-n112-k8 | 111 | 8 | ~12-15 | 100+ |
| X-n469-k26 | 469 | 26 | ~25-30 | 200+ |

---

## Recommended Enhancements

### Enhancement #1: Increase Generations
**Why:** Currently converges at Gen 20, Gen 21-50 don't improve
**How:** Change `generations = 100` in main.py
**Expected Result:** May find additional improvements (1-5% better fitness)
```python
generations = 100  # from 50
```

### Enhancement #2: Improve Mutation Diversity
**Why:** After convergence, need more exploration
**How:** Increase mutation probability
**Expected Result:** Escape local optima, find better solutions
```python
mutation_probability = 0.15  # from 0.1 (50% more mutations)
```

### Enhancement #3: Adaptive Parameter Tuning
**Why:** Static parameters may not be optimal for all problems
**How:** Implement adaptive rates based on generation number
```python
def adaptive_mutation_rate(generation, max_generations):
    # High mutation early (exploration)
    # Low mutation late (exploitation)
    return 0.2 * (1 - generation/max_generations) + 0.05
```

### Enhancement #4: Simulated Annealing Integration
**Why:** Occasionally accept worse solutions to escape local optima
**How:** 
```python
# Accept worse solution with probability that decreases over time
temperature = initial_temp * (1 - generation/max_generations)
accept_worse_prob = exp((new_fitness - old_fitness) / temperature)
```

### Enhancement #5: Multi-Objective Optimization (Pareto Front)
**Why:** Current solution optimizes aggregate fitness; may miss diverse solutions
**How:** Track all non-dominated solutions
```python
# Instead of just best solution:
pareto_front = []  # Solutions not dominated by any other
for solution in population:
    if not dominated_by(solution, pareto_front):
        pareto_front.append(solution)
```

### Enhancement #6: Charged Routing (Smart Charging)
**Why:** Currently simplified penalty model for battery
**How:** Auto-insert charging stations when battery critical
```python
if battery < battery_capacity * 0.3:  # Less than 30%
    # Find nearest station
    # Route to station first
    # Then continue to destination
```

### Enhancement #7: Constraint Validation
**Why:** Verify all constraints satisfied (not just fitness)
**How:** Add comprehensive validation
```python
def validate_solution(chromosome):
    - Check all customers served
    - Verify no vehicle capacity exceeded
    - Ensure battery sufficient for all routes
    - Confirm time windows respected (if any)
    return True/False
```

---

## Debugging & Troubleshooting

### Issue: Fitness Not Improving After Gen 20
**Diagnosis:**
```python
# Check fitness history
print(ga.best_fitness_history)
# If all values same after Gen 20 -> convergence reached

# Check mutation effectiveness
print("Last 10 mutations:")
for gen in range(40, 50):
    print(f"Gen {gen}: {mutations_performed[gen]}")
```

**Solution:**
- Increase `mutation_probability` to 0.2
- Use adaptive rates that increase later generations
- Implement restart mechanism every N generations

### Issue: All Solutions Infeasible
**Diagnosis:**
```python
# Check if battery_capacity too small
print(f"Max distance in any edge: {max_single_edge_distance}")
print(f"Battery capacity: {battery_capacity}")
print(f"Consumption rate: {consumption_rate}")

if max_single_edge_distance * consumption_rate > battery_capacity:
    print("Problem infeasible with current parameters!")
```

**Solution:**
- Increase battery_capacity
- Decrease consumption_rate
- Add more charging stations

### Issue: Single-Customer Routes Appearing
**Diagnosis:**
```python
# Check routes in best solution
for i, route in enumerate(best_routes):
    customers = [n for n in route if n.startswith('C')]
    print(f"Route {i}: {len(customers)} customers")
    if len(customers) == 1:
        print("  WARNING: Single-customer route!")
```

**Solution:**
- Increase single-customer penalty from 0.5 to 1.0
- Implement forced consolidation in crossover operator
- Enhance mutation to avoid breaking up multi-customer routes

---

## Code Structure Overview

```
main.py
├── Class: GeneticAlgorithmEVRP
├── __init__: Load EVRP file, compute distances
├── evaluate_fitness: Call fitness_function for all chromosomes
├── perform_crossover: Apply BCRC crossover
├── perform_mutation: Apply inter/intra-depot mutations
├── run_generation: Single GA iteration
├── run: Main loop (50 generations)
└── print_results: Display final output

fitness.py
├── fitness_function: Main evaluation function
├── extract_id: String to integer conversion (D1→1)
└── get_distance: Dictionary lookup with format conversion

generatePopulation.py
├── parse_evrp_file: Read EVRP file
├── generate_initial_chromosome: Create single solution
└── generate_initial_population: Create population

mutation.py
├── intra_depot_mutation: Reorder within route
└── inter_depot_mutation: Move customer between routes

crossover.py
├── bcrc_crossover: Best-cost route crossover
└── crossover_route_based: Alternative crossover

selection.py
├── get_elites: Identify best solutions
├── run_tournament: Tournament selection
└── selection: Combined elite + tournament

utlis.py
├── calculate_distance_matrix: Precompute all distances
└── euclidean_distance: Distance formula
```

---

## Next Session Checklist

- [ ] Test with larger problem instances (X-n469-k26, etc.)
- [ ] Implement adaptive parameter tuning
- [ ] Add Pareto front tracking for multi-objective analysis
- [ ] Create visualization of routes (matplotlib/plotly)
- [ ] Benchmark against known optimal solutions
- [ ] Document results in IEEE format for publication

---

## Contact & Support

For issues or enhancements:
1. Check TECHNICAL_ANALYSIS.md for detailed bug explanations
2. Review IMPROVEMENTS_SUMMARY.md for changes made
3. Run verify_solution.py to validate current solution
4. Enable verbose logging in main.py for debugging

Good luck with your EVRP optimization!
