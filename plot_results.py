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

        # Contoh nama folder:
        # dag_0_n10_ccr0.1_p4_shape0.5
        m = re.search(r"_n(\d+)_ccr([0-9.]+)_p(\d+)_", folder)
        if m:
            n = int(m.group(1))
            ccr = float(m.group(2))
            processors = int(m.group(3))
        else:
            n = None
            ccr = None
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
                "ccr": ccr,
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


def plot_metric_vs_param(
    aggregated,
    param_name,
    metrics_order,
    out_dir,
    categorical_x=False,
    x_labels=None,
):
    # kunci param (n / processors / ccr)
    keys = sorted(aggregated.keys())
    if not keys:
        return

    # kalau mau jarak X rata: pakai index 0..len-1
    if categorical_x:
        x_plot = list(range(len(keys)))
        if x_labels is None:
            x_labels = keys
    else:
        x_plot = keys

    # styling per algoritma
    algo_styles = {
        "HEFT": {"color": "red", "marker": "^"},
        "GA": {"color": "orange", "marker": "o"},
        # kalau nanti nambah algo lain, tambahin di sini
    }

    # kumpulin nama algoritma yang ada
    algos = set()
    for v in aggregated.values():
        algos.update(v.keys())
    algos = sorted(algos)

    for metric in metrics_order:
        plt.figure(figsize=(4.5, 3))  # ukuran mirip grafik paper

        for algo in algos:
            y_vals = []
            for k in keys:
                y_vals.append(aggregated[k].get(algo, {}).get(metric, float("nan")))

            style = algo_styles.get(algo, {})
            plt.plot(
                x_plot,
                y_vals,
                label=algo,
                marker=style.get("marker", "o"),
                color=style.get("color", None),
                linewidth=2,
                markersize=6,
            )

        plt.grid(True, linestyle="--", alpha=0.4)
        plt.ylabel(metric)
        plt.title(f"{metric} vs {param_name}")

        # handle label X
        if categorical_x:
            plt.xticks(x_plot, x_labels)
        else:
            plt.xticks(x_plot, keys)
        plt.xlabel(param_name)

        plt.legend(frameon=False)
        plt.tight_layout()

        os.makedirs(out_dir, exist_ok=True)
        safe_metric = metric.replace(" ", "_")
        fname = f"{safe_metric}_vs_{param_name}.png"
        fpath = os.path.join(out_dir, fname)

        plt.savefig(fpath, dpi=300)
        plt.close()


if __name__ == "__main__":
    runs = load_results_with_meta()
    if not runs:
        print("No results found in data/dags. Jalankan main.py dulu.")
    else:
        out_dir = "results_preview"
        os.makedirs(out_dir, exist_ok=True)

        # ambil urutan metrik dari satu sample
        sample_metrics = next(iter(runs[0]["results"].values()))
        metrics_order = list(sample_metrics.keys())

        # n (jumlah tugas) → pakai X numeric biasa
        agg_n = aggregate_by_param(runs, "n")
        plot_metric_vs_param(
            agg_n,
            "n",
            metrics_order,
            out_dir,
            categorical_x=False,
        )

        # processors → juga numeric biasa
        agg_p = aggregate_by_param(runs, "processors")
        plot_metric_vs_param(
            agg_p,
            "processors",
            metrics_order,
            out_dir,
            categorical_x=False,
        )

        # CCR → X diratakan (kategori), label tetap nilai CCR
        agg_ccr = aggregate_by_param(runs, "ccr")
        ccr_keys = sorted(agg_ccr.keys())
        ccr_labels = [("{:.2g}".format(v)).rstrip("0").rstrip(".") for v in ccr_keys]

        plot_metric_vs_param(
            agg_ccr,
            "CCR",
            metrics_order,
            out_dir,
            categorical_x=True,
            x_labels=ccr_labels,
        )

        print(f"Gambar disimpan ke folder: {out_dir}")
