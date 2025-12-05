# evaluate.py
import math
from collections import deque

import numpy as np

# Harga sewa instance per jam (bisa kamu sesuaikan dengan skenario di skripsi)
C_INST_PER_HOUR = 0.1

# Failure rate dasar prosesor (parameter model reliabilitas)
LAMBDA_0 = 1e-5


def compute_task_times(proc_assignment, tasks, edges, processors):
    """
    Hitung AST (Actual Start Time) dan AFT (Actual Finish Time) setiap task
    berdasarkan:
    - struktur DAG (edges)
    - mapping task -> processor (proc_assignment)
    - satu queue per prosesor, non-preemptive
    - communication cost jika producer dan consumer beda prosesor
    """
    n = len(tasks)

    preds = {i: [] for i in range(n)}
    succs = {i: [] for i in range(n)}
    comm = {}

    for e in edges:
        s = e["src"]
        d = e["dst"]
        c = e.get("comm", 0.0)
        preds[d].append(s)
        succs[s].append(d)
        comm[(s, d)] = c

    # topological order
    indeg = [len(preds[i]) for i in range(n)]
    q = deque([i for i in range(n) if indeg[i] == 0])
    order = []

    while q:
        u = q.popleft()
        order.append(u)
        for v in succs[u]:
            indeg[v] -= 1
            if indeg[v] == 0:
                q.append(v)

    # fallback kalau entah kenapa DAG tidak valid
    if len(order) != n:
        order = list(range(n))

    avail_time = [0.0] * processors  # kapan tiap prosesor ready
    AST = [0.0] * n
    AFT = [0.0] * n
    cost_table = [t["cost"] for t in tasks]

    for t in order:
        p = proc_assignment.get(t, 0)

        # tunggu semua predecessor selesai (plus komunikasi)
        ready = 0.0
        for pred in preds[t]:
            pred_proc = proc_assignment.get(pred, 0)
            comm_time = comm.get((pred, t), 0.0) if pred_proc != p else 0.0
            ready = max(ready, AFT[pred] + comm_time)

        start_time = max(avail_time[p], ready)
        AST[t] = start_time
        finish = start_time + cost_table[t]
        AFT[t] = finish
        avail_time[p] = finish

    return AST, AFT


def evaluate_schedule(proc_assignment, tasks, edges, processors):
    # ---------------- MAKESPAN & LOAD PER PROSESOR ----------------
    loads = [0.0] * processors
    for task_id, proc in proc_assignment.items():
        cost = tasks[task_id]["cost"]
        loads[proc] += cost

    makespan = max(loads) if loads else 0.0

    # ---------------- ENERGY (MODEL HUANG, DISEDERHANAKAN) --------
    # P = Ps + c * f^3, dengan f_max = 1 dan semua task jalan di f_max
    Ps = 1.0
    c = 1.0
    f = 1.0
    P = Ps + c * (f ** 3)

    total_T = sum(tasks[tid]["cost"] for tid in proc_assignment.keys())
    energy = P * total_T

    # ---------------- AST & AFT UNTUK COST & RELIABILITY ----------
    AST, AFT = compute_task_times(proc_assignment, tasks, edges, processors)

    # ---------------- COST (MODEL TOUSSI: HOURLY-BASED) -----------
    total_cost = 0.0
    for p in range(processors):
        task_ids = [tid for tid, pr in proc_assignment.items() if pr == p]
        if not task_ids:
            continue

        start = min(AST[tid] for tid in task_ids)
        end = max(AFT[tid] for tid in task_ids)
        duration_hours = (end - start) / 3600.0

        total_cost += duration_hours * C_INST_PER_HOUR

    cost_cloud = total_cost

    # ---------------- RELIABILITY (MODEL POISSON) -----------------
    # R_i = exp(-lambda0 * t_i), t_i = AFT_i - AST_i
    log_Rg = 0.0
    for tid in proc_assignment.keys():
        exec_time = AFT[tid] - AST[tid]
        log_Rg += -LAMBDA_0 * exec_time

    reliability = math.exp(log_Rg)

    # ---------------- LOAD BALANCING (VARIANSI BEBAN) -------------
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