# dag_generator.py
import csv 
import random
import os
from config import CONFIG


def generate_single_dag(n, out_degree_range, beta):
    tasks = []
    edges = []

    # generate task cost
    for i in range(n):
        base = random.randint(10, 50)
        low = base * (1 - beta / 2)
        high = base * (1 + beta / 2)
        cost = round(random.uniform(low, high), 2)
        tasks.append({"task": i, "cost": cost})

    # generate edges (DAG forward only)
    for i in range(n):
        out_deg = random.choice(out_degree_range)
        possible_targets = list(range(i + 1, n))
        random.shuffle(possible_targets)
        for t in possible_targets[:out_deg]:
            edges.append({
                "src": i,
                "dst": t,
                "comm": random.randint(1, 10)
            })

    return tasks, edges


def save_dag(tasks, edges, folder, meta):
    os.makedirs(folder, exist_ok=True)

    with open(f"{folder}/tasks.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["task", "cost"])
        for t in tasks:
            writer.writerow([t["task"], t["cost"]])

    with open(f"{folder}/edges.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["src", "dst", "comm"])
        for e in edges:
            writer.writerow([e["src"], e["dst"], e["comm"]])

    # metadata
    with open(f"{folder}/meta.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["processors", "ccr", "shape_alpha"])
        writer.writerow([meta["processors"], meta["ccr"], meta["shape_alpha"]])


def generate_all_dags():
    out_degree_range = CONFIG["out_degree_range"]
    beta = CONFIG["beta"]

    idx = 0
    for n in CONFIG["number_of_nodes"]:
        for ccr in CONFIG["ccr"]:
            for proc in CONFIG["processors"]:
                for shape in CONFIG["shape_alpha"]:

                    folder = (
                        f"data/dags/dag_{idx}_n{n}_ccr{ccr}_p{proc}_shape{shape}"
                    )

                    tasks, edges = generate_single_dag(
                        n,
                        out_degree_range,
                        beta
                    )

                    save_dag(tasks, edges, folder, {
                        "processors": proc,
                        "ccr": ccr,
                        "shape_alpha": shape
                    })

                    idx += 1

    print(f"Generated {idx} DAG variations.")


if __name__ == "__main__":
    generate_all_dags()