# main.py
import csv
import os
from heft import heft_schedule
from ga_scheduler import ga_schedule
from evaluate import evaluate_schedule


def load_tasks_edges(folder):
    tasks = []
    edges = []

    # load tasks.csv
    with open(os.path.join(folder, "tasks.csv")) as f:
        reader = csv.DictReader(f)
        for row in reader:
            tasks.append({
                "task": int(row["task"]),
                "cost": float(row["cost"]),
            })

    # load edges.csv
    with open(os.path.join(folder, "edges.csv")) as f:
        reader = csv.DictReader(f)
        for row in reader:
            edges.append({
                "src": int(row["src"]),
                "dst": int(row["dst"]),
                "comm": float(row.get("comm", 0) or 0.0),
            })

    return tasks, edges


def load_meta(folder):
    meta_path = os.path.join(folder, "meta.csv")
    processors = 1

    if os.path.exists(meta_path):
        with open(meta_path) as f:
            reader = csv.DictReader(f)
            row = next(reader, None)
            if row and "processors" in row:
                processors = int(row["processors"])

    return processors


def save_results(results, out_path):
    """
    results: dict
        {
            "HEFT": {metrik...},
            "GA": {metrik...}
        }
    """
    if not results:
        return

    sample_metrics = next(iter(results.values()))
    fieldnames = ["algorithm"] + list(sample_metrics.keys())

    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for algo, metrics in results.items():
            row = {"algorithm": algo}
            row.update(metrics)
            writer.writerow(row)


def main(root="data/dags"):
    if not os.path.isdir(root):
        print(f"Folder {root} tidak ditemukan.")
        return

    for folder in sorted(os.listdir(root)):
        full_path = os.path.join(root, folder)
        if not os.path.isdir(full_path):
            continue

        tasks_path = os.path.join(full_path, "tasks.csv")
        edges_path = os.path.join(full_path, "edges.csv")
        meta_path = os.path.join(full_path, "meta.csv")

        # skip kalau file pentingnya nggak lengkap
        if not (os.path.exists(tasks_path) and os.path.exists(edges_path) and os.path.exists(meta_path)):
            continue

        tasks, edges = load_tasks_edges(full_path)
        processors = load_meta(full_path)

        heft_assign, _ = heft_schedule(tasks, edges, processors)
        ga_ind, _ = ga_schedule(tasks, edges, processors)
        ga_assign = {i: ga_ind[i] for i in range(len(tasks))}

        results = {
            "HEFT": evaluate_schedule(heft_assign, tasks, edges, processors),
            "GA": evaluate_schedule(ga_assign, tasks, edges, processors),
        }

        out_file = os.path.join(full_path, "results.csv")
        save_results(results, out_file)
        print(f"Saved result: {out_file}")


if __name__ == "__main__":
    main()