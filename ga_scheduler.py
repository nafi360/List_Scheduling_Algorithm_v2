# ga_scheduler.py
import random

def compute_load(individual, tasks, processors):
    loads = [0] * processors
    for i, p in enumerate(individual):
        loads[p] += tasks[i]["cost"]
    return loads

def fitness(individual, tasks, processors):
    return max(compute_load(individual, tasks, processors))

def ga_schedule(tasks, edges, processors=4, pop_size=30, gens=40, mut_rate=0.1):
    n = len(tasks)

    population = [
        [random.randint(0, processors - 1) for _ in range(n)]
        for _ in range(pop_size)
    ]

    for _ in range(gens):
        scored = sorted(
            population,
            key=lambda ind: fitness(ind, tasks, processors)
        )

        parents = scored[:pop_size // 2]
        new_population = parents.copy()

        while len(new_population) < pop_size:
            p1, p2 = random.sample(parents, 2)
            cut = random.randint(1, n - 1)
            child = p1[:cut] + p2[cut:]

            if random.random() < mut_rate:
                idx = random.randint(0, n - 1)
                child[idx] = random.randint(0, processors - 1)

            new_population.append(child)

        population = new_population

    best = min(population, key=lambda ind: fitness(ind, tasks, processors))
    return best, fitness(best, tasks, processors)