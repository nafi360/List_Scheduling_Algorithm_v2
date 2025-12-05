# plot_results.py
import csv
import os
import re
import matplotlib.pyplot as plt


def load_results_with_meta(root="data/dags"):
    runs = []

    if not os.path.isdir(root):
        return runs

    for folder in sorted(os.listdir(root)):
        full_folder = os.path.join(root, folder)
        res_path = os.path.join(full_folder, "results.csv")
        if not os.path.isfile(res_path):
            continue

        # Ambil n & processors dari nama folder
        m = re.search(r"_n(\d+)_.*_p(\d+)_", folder)
        if m:
            n = int(m.group(1))
            processors = int(m.group(2))
        else:
            n = None
            processors = None

        # load hasil per algoritma
        with open(res_path) as f:
            reader = csv.DictReader(f)
            algo_results = {}
            for row in reader:
                algo = row.get("algorithm")
                if not algo:
                    continue
                metrics = {k: float(v) for k, v in row.items() if k != "algorithm"}
                algo_results[algo] = metrics

        if algo_results:
            runs.append({
                "folder": folder,
                "n": n,
                "processors": processors,
                "results": algo_results,
            })

    return runs


def aggregate_by_param(runs, param):
    grouped = {}
    for r in runs:
        key = r.get(param)
        if key is None:
            continue

        if key not in grouped:
            grouped[key] = {}

        for algo, metrics in r["results"].items():
            if algo not in grouped[key]:
                grouped[key][algo] = {m: [] for m in metrics}
            for m, v in metrics.items():
                grouped[key][algo][m].append(v)

    aggregated = {}
    for key, algo_dict in grouped.items():
        aggregated[key] = {}
        for algo, metric_lists in algo_dict.items():
            aggregated[key][algo] = {
                m: sum(vals) / len(vals) for m, vals in metric_lists.items()
            }
    return aggregated


def plot_metric_vs_param(aggregated, param_name, metrics_order, out_dir):
    x_vals = sorted(aggregated.keys())
    if not x_vals:
        return

    for metric in metrics_order:
        plt.figure()

        heft_y = []
        ga_y = []

        for x in x_vals:
            algo_dict = aggregated[x]
            heft_y.append(algo_dict.get("HEFT", {}).get(metric, float("nan")))
            ga_y.append(algo_dict.get("GA", {}).get(metric, float("nan")))

        plt.plot(x_vals, heft_y, marker="o", label="HEFT")
        plt.plot(x_vals, ga_y, marker="o", label="GA")

        plt.grid(True, linestyle="--", alpha=0.5)
        plt.xlabel(param_name)
        plt.ylabel(metric)
        plt.title(f"{metric} vs {param_name}")
        plt.legend()
        plt.tight_layout()

        os.makedirs(out_dir, exist_ok=True)
        safe_metric = metric.replace(" ", "_")
        fname = f"{safe_metric}_vs_{param_name}.png"
        fpath = os.path.join(out_dir, fname)

        plt.savefig(fpath, dpi=300)
        plt.close()   # FIX WAJIB


if __name__ == "__main__":
    runs = load_results_with_meta()
    if not runs:
        print("No results found in data/dags. Jalankan main.py dulu.")
    else:
        out_dir = "results_preview"
        os.makedirs(out_dir, exist_ok=True)

        sample_metrics = next(iter(runs[0]["results"].values()))
        metrics_order = list(sample_metrics.keys())

        agg_n = aggregate_by_param(runs, "n")
        plot_metric_vs_param(agg_n, "n", metrics_order, out_dir)

        agg_p = aggregate_by_param(runs, "processors")
        plot_metric_vs_param(agg_p, "processors", metrics_order, out_dir)

        print(f"Gambar disimpan ke folder: {out_dir}")