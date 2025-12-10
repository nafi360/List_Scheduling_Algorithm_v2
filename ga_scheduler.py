import random
from typing import List, Tuple
from evaluate import compute_task_times


def compute_priorities(tasks, edges) -> List[float]:
    """
    Step 2: Tentukan prioritas tugas.
    Di sini dipakai 'upward rank' ala HEFT:
    rank_u(i) = cost(i) + max(rank_u(child)) untuk semua successor.
    """
    n = len(tasks)
    succs = {i: [] for i in range(n)}
    for e in edges:
        succs[e["src"]].append(e["dst"])

    cost = [t["cost"] for t in tasks]
    memo = {}

    def rank_u(tid: int) -> float:
        if tid in memo:
            return memo[tid]
        if not succs[tid]:
            memo[tid] = cost[tid]
        else:
            memo[tid] = cost[tid] + max(rank_u(ch) for ch in succs[tid])
        return memo[tid]

    priorities = [rank_u(i) for i in range(n)]
    return priorities


def init_population(pop_size: int, n: int, processors: int, priorities, tasks) -> List[List[int]]:
    """
    Step 3–4: Prosedur pengkodean & penetapan prosesor.
    Kromosom = list panjang n, nilai gen = index prosesor.
    Inisialisasi: tugas dijadwalkan urut prioritas tinggi -> rendah.
    """
    order = sorted(range(n), key=lambda i: priorities[i], reverse=True)
    population = []

    for _ in range(pop_size):
        loads = [0.0] * processors
        individual = [0] * n

        for t in order:
            # Kebanyakan pilih prosesor dengan beban minimum (greedy),
            # kadang-kadang random biar ada keberagaman.
            if processors > 1 and random.random() < 0.7:
                p = min(range(processors), key=lambda x: loads[x])
            else:
                p = random.randint(0, processors - 1)

            individual[t] = p
            loads[p] += tasks[t]["cost"]

        population.append(individual)

    return population


def fitness(individual: List[int], tasks, edges, processors: int) -> float:
    """
    Step 5: Fungsi fitness.
    Pakai MAKESPAN berbasis DAG (compute_task_times dari evaluate.py).
    """
    proc_assignment = {i: individual[i] for i in range(len(individual))}
    _, aft = compute_task_times(proc_assignment, tasks, edges, processors)
    makespan = max(aft) if aft else 0.0
    return makespan


def tournament_select(population: List[List[int]], tasks, edges, processors: int, k: int = 3) -> List[int]:
    """
    Step 6: Seleksi (tournament selection).
    """
    contenders = random.sample(population, k)
    best = min(contenders, key=lambda ind: fitness(ind, tasks, edges, processors))
    return best


def crossover(parent1: List[int], parent2: List[int]) -> Tuple[List[int], List[int]]:
    """
    Step 7: Crossover satu titik (one-point crossover).
    """
    n = len(parent1)
    if n <= 1:
        return parent1[:], parent2[:]

    cut = random.randint(1, n - 1)
    child1 = parent1[:cut] + parent2[cut:]
    child2 = parent2[:cut] + parent1[cut:]
    return child1, child2


def mutate(individual: List[int], processors: int, mut_rate: float) -> List[int]:
    """
    Step 8: Mutasi (random reset gene dengan probabilitas mut_rate per gen).
    """
    n = len(individual)
    for i in range(n):
        if random.random() < mut_rate:
            individual[i] = random.randint(0, processors - 1)
    return individual


def ga_schedule(tasks, edges, processors: int = 4, pop_size: int = 30, gens: int = 40, mut_rate: float = 0.1):
    """
    Mengimplementasikan 10 tahap GA:

    1) input           -> parameter fungsi (tasks, edges, processors, pop_size, gens, mut_rate)
    2) prioritas tugas -> compute_priorities
    3) pengkodean      -> kromosom = list penugasan task -> prosesor
    4) assign prosesor -> init_population + decoding di fitness
    5) fitness         -> fungsi fitness() (makespan)
    6) seleksi         -> tournament_select()
    7) crossover       -> crossover()
    8) mutasi          -> mutate()
    9) iterasi         -> loop 'gens' generasi
    10) output         -> individu terbaik & makespan-nya
    """
    n = len(tasks)
    if n == 0:
        return [], 0.0

    # Step 2: prioritas tugas
    priorities = compute_priorities(tasks, edges)

    # Step 3–4: inisialisasi populasi
    population = init_population(pop_size, n, processors, priorities, tasks)

    # Tracking solusi terbaik global
    best_individual = None
    best_fitness = float("inf")

    # Step 9: iterasi GA
    for _ in range(gens):
        # Hitung fitness semua individu
        scored = [(ind, fitness(ind, tasks, edges, processors)) for ind in population]
        scored.sort(key=lambda x: x[1])

        # Update solusi terbaik
        if scored[0][1] < best_fitness:
            best_fitness = scored[0][1]
            best_individual = scored[0][0][:]

        # Elitism: bawa 1 individu terbaik ke generasi berikutnya
        new_population: List[List[int]] = [scored[0][0][:]]

        # Bangun populasi baru via seleksi, crossover, mutasi
        while len(new_population) < pop_size:
            p1 = tournament_select(population, tasks, edges, processors)
            p2 = tournament_select(population, tasks, edges, processors)

            c1, c2 = crossover(p1, p2)
            mutate(c1, processors, mut_rate)
            mutate(c2, processors, mut_rate)

            new_population.append(c1)
            if len(new_population) < pop_size:
                new_population.append(c2)

        population = new_population

    # Step 10: output -> kromosom terbaik & makespan-nya
    return best_individual, best_fitness