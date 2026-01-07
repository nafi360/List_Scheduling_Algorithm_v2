# config.py
# Parameter untuk random DAG generator

CONFIG = {
    "number_of_nodes": [10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
    "ccr": [0.1, 0.5, 0.8, 1, 2, 5, 8, 10],
    "processors": [4, 8, 16, 32, 64],
    "shape_alpha": [0.5, 0.8, 1, 2, 4],
    "out_degree_range": [1, 2, 3, 4],
    "beta": 0.5
}

# variasi yang dihasilkan: 10 (nodes) x 8 (ccr) x 5 (processors) x 5 (shape_alpha) = 2000 DAGs