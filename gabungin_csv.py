import pandas as pd
from pathlib import Path

ROOT = Path("data/dags")  # sesuaikan path

dfs = []

for folder in ROOT.iterdir():
    if folder.is_dir():
        csv_path = folder / "results.csv"
        if csv_path.exists():
            df = pd.read_csv(csv_path)
            df["folder_name"] = folder.name
            dfs.append(df)

final_df = pd.concat(dfs, ignore_index=True)
final_df.to_csv("results_gabungan.csv", index=False)

print("Done. Total rows:", len(final_df))