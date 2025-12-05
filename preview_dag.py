import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from collections import defaultdict

# ==========================
# 1. LOAD DATA
# ==========================
# Pastikan nama file sama dengan file kamu
edges = pd.read_csv("data/dags/dag_0_n10_ccr0.1_p4_shape0.5/edges.csv")   # kolom: src, dst, comm
tasks = pd.read_csv("data/dags/dag_0_n10_ccr0.1_p4_shape0.5/tasks.csv")   # kolom: task, cost

# Paksa ID task & edge jadi integer biar gak ada ".0"
tasks["task"] = tasks["task"].astype(int)
edges["src"] = edges["src"].astype(int)
edges["dst"] = edges["dst"].astype(int)

# ==========================
# 2. BANGUN DAG
# ==========================
G = nx.DiGraph()

# Tambah node
for _, row in tasks.iterrows():
    G.add_node(row["task"], cost=row.get("cost", None))

# Tambah edge + atribut comm
for _, row in edges.iterrows():
    G.add_edge(row["src"], row["dst"], comm=row["comm"])

# Cek DAG atau bukan (opsional, buat jaga-jaga)
if not nx.is_directed_acyclic_graph(G):
    print("Warning: Graph bukan DAG. Hasil layout mungkin kacau.")

# ==========================
# 3. HITUNG LEVEL / LAYER MANUAL
# ==========================
# Level = jarak maksimum dari source (topological based)
level = {}
topo_order = list(nx.topological_sort(G))

for n in topo_order:
    preds = list(G.predecessors(n))
    if preds:
        level[n] = max(level[p] + 1 for p in preds)
    else:
        level[n] = 0  # node tanpa predecessor = level 0

# Group node per level
level_nodes = defaultdict(list)
for n, lev in level.items():
    level_nodes[lev].append(n)

# ==========================
# 4. TENTUKAN POSISI (x, y) PER LEVEL
# ==========================
pos = {}
for lev, nodes_at_level in level_nodes.items():
    # Biar konsisten, urutkan node-nya
    nodes_at_level = sorted(nodes_at_level)

    k = len(nodes_at_level)
    # X disebar dari 0 ke 1
    if k == 1:
        xs = [0.5]
    else:
        xs = [i / (k - 1) for i in range(k)]

    # Y berdasarkan level (atas ke bawah)
    y = -lev
    for x, n in zip(xs, nodes_at_level):
        pos[n] = (x, y)

# ==========================
# 5. GAMBAR DAG
# ==========================
plt.figure(figsize=(4, 6))

# Node: bulat putih, pinggir hitam
nx.draw_networkx_nodes(
    G, pos,
    node_size=900,
    node_color="white",
    edgecolors="black",
    linewidths=1.5
)

# Edge: panah
nx.draw_networkx_edges(
    G, pos,
    arrows=True,
    arrowstyle="-|>",
    arrowsize=15,
    width=1
)

# Label node: ID task tanpa ".0"
node_labels = {n: str(n) for n in G.nodes()}
nx.draw_networkx_labels(
    G, pos,
    labels=node_labels,
    font_size=10
)

# Label edge: comm di tengah panah
edge_labels = {(u, v): d["comm"] for u, v, d in G.edges(data=True)}
nx.draw_networkx_edge_labels(
    G, pos,
    edge_labels=edge_labels,
    font_size=8,
    label_pos=0.5
)

plt.axis("off")
plt.tight_layout()
plt.show()