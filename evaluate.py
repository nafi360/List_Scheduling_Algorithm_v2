# evaluate.py
import math
from collections import deque
from typing import Dict, List, Tuple, Union

import numpy as np

# Harga sewa instance per jam (silakan sesuaikan skenario skripsi)
C_INST_PER_HOUR = 0.1

# Failure rate dasar prosesor
LAMBDA_0 = 1e-5

# Parameter model energi (sederhana tapi jadwal-dependent)
P_IDLE = 50.0       # “leakage” power saat idle (W, skala relatif)
P_DYN_MAX = 100.0   # tambahan power saat utilisation = 1


AssignmentType = Union[Dict[int, int], List[int]]


def _build_graph(n: int, edges) -> Tuple[Dict[int, List[int]], Dict[int, List[int]], Dict[Tuple[int, int], float]]:
    """Bangun struktur DAG: preds, succs, dan biaya komunikasi."""
    preds = {i: [] for i in range(n)}
    succs = {i: [] for i in range(n)}
    comm: Dict[Tuple[int, int], float] = {}

    for e in edges:
        s = int(e["src"])
        d = int(e["dst"])
        c = float(e.get("comm", 0.0) or 0.0)

        preds[d].append(s)
        succs[s].append(d)
        comm[(s, d)] = c

    return preds, succs, comm


def _topological_order(n: int, succs: Dict[int, List[int]]) -> List[int]:
    """Topological sort sederhana."""
    indeg = [0] * n
    for u in range(n):
        for v in succs[u]:
            indeg[v] += 1

    q = deque(i for i in range(n) if indeg[i] == 0)
    order = []

    while q:
        u = q.popleft()
        order.append(u)
        for v in succs[u]:
            indeg[v] -= 1
            if indeg[v] == 0:
                q.append(v)

    if len(order) != n:
        raise ValueError("Graf tugas bukan DAG (ada siklus / task nyangkut).")

    return order


def compute_task_times(
    proc_assignment: AssignmentType,
    tasks,
    edges,
    processors: int,
):
    """
    Hitung AST (Actual Start Time) dan AFT (Actual Finish Time) setiap task
    dengan jadwal yang SUDAH ditentukan (HEFT atau GA).

    proc_assignment: dict/list, task -> prosesor
    tasks: list of dict, minimal punya key "cost"
    edges: list of dict, minimal punya "src", "dst", optional "comm"
    """
    n = len(tasks)
    if n == 0:
        return [], []

    preds, succs, comm = _build_graph(n, edges)
    topo = _topological_order(n, succs)

    # Normalisasi assignment ke bentuk list
    if isinstance(proc_assignment, dict):
        assignment = [int(proc_assignment[i]) for i in range(n)]
    else:
        assignment = [int(p) for p in proc_assignment]

    proc_avail = [0.0] * processors
    ast = [0.0] * n
    aft = [0.0] * n

    for t in topo:
        p = assignment[t]
        ready_pred = 0.0

        # constraint dependency + komunikasi
        for pred in preds[t]:
            pred_p = assignment[pred]
            comm_time = comm.get((pred, t), 0.0) if pred_p != p else 0.0
            ready_pred = max(ready_pred, aft[pred] + comm_time)

        start = max(proc_avail[p], ready_pred)
        finish = start + float(tasks[t]["cost"])

        ast[t] = start
        aft[t] = finish
        proc_avail[p] = finish

    return ast, aft

def evaluate_schedule(proc_assignment, tasks, edges, processors):
    n = len(tasks)
    if n == 0:
        return {
            "makespan": 0.0,
            "energy": 0.0,
            "cost": 0.0,
            "reliability": 1.0,
            "load_balance": 0.0,
        }

    # ---------------- WAKTU TUGAS (AST & AFT) ----------------
    AST, AFT = compute_task_times(proc_assignment, tasks, edges, processors)
    makespan = max(AFT) if AFT else 0.0

    # ---------------- BEBAN PER PROSESOR (DALAM WAKTU) ------- 
    loads = [0.0] * processors
    for tid, p in proc_assignment.items():
        duration = AFT[tid] - AST[tid]   # waktu aktif task di prosesor
        loads[p] += duration

    # Utilisation 0..1
    if makespan > 0:
        util = [load / makespan for load in loads]
    else:
        util = [0.0] * processors

    # ---------------- ENERGY (BERBASIS UTILISATION) ---------- 
    P_IDLE = 50.0      # bebas, skala relatif
    P_DYN_MAX = 100.0  # bebas, skala relatif

    energy = 0.0
    for u in util:
        power = P_IDLE + P_DYN_MAX * (u ** 2)
        energy += power * makespan

    # ---------------- COST (HOURLY-BASED PER PROSESOR) ------- 
    total_cost = 0.0
    for p in range(processors):
        task_ids = [tid for tid, pr in proc_assignment.items() if pr == p]
        if not task_ids:
            continue

        start = min(AST[tid] for tid in task_ids)
        end = max(AFT[tid] for tid in task_ids)
        duration_hours = max(0.0, (end - start) / 3600.0)

        total_cost += duration_hours * C_INST_PER_HOUR

    cost_cloud = total_cost

    # ---------------- RELIABILITY (FUNCTION OF UTIL) --------- 
    log_Rg = 0.0
    for u in util:
        lam_p = LAMBDA_0 * (1.0 + 4.0 * u)
        log_Rg += -lam_p * makespan

    reliability = math.exp(log_Rg)

    # ---------------- LOAD BALANCING (VARIANSI BEBAN) -------- 
    if processors > 1:
        mean_load = float(np.mean(loads))
        variance = sum((l - mean_load) ** 2 for l in loads) / (processors - 1)
        load_balance = math.sqrt(variance)
    else:
        load_balance = 0.0

    return {
        "makespan": makespan,
        "energy": energy,
        "cost": cost_cloud,
        "reliability": reliability,
        "load_balance": load_balance,
    }