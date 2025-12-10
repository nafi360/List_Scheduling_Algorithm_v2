# heft.py

from typing import Dict, List, Tuple


def compute_ranku(
    task: int,
    succs: Dict[int, List[int]],
    cost_table: List[float],
    comm: Dict[Tuple[int, int], float],
    memo: Dict[int, float],
) -> float:
    """
    Upward rank ala HEFT:
    rank_u(i) = w_i + max_{j ∈ succ(i)} ( c_{ij} + rank_u(j) )

    - w_i  : waktu komputasi task i
    - c_ij : waktu komunikasi dari i ke j
    """
    if task in memo:
        return memo[task]

    if not succs[task]:
        # task tanpa successor
        memo[task] = cost_table[task]
    else:
        memo[task] = cost_table[task] + max(
            comm.get((task, child), 0.0)
            + compute_ranku(child, succs, cost_table, comm, memo)
            for child in succs[task]
        )

    return memo[task]


def heft_schedule(tasks, edges, processors: int = 4):
    """
    Implementasi HEFT sesuai pernyataan kamu:

    1) Menentukan prioritas setiap tugas berdasarkan urutan eksekusi
       dan ketergantungan antar tugas (upward rank).
    2) Menetapkan tugas ke prosesor yang memberikan waktu penyelesaian
       (finish time) paling cepat, dengan memperhitungkan:
       - waktu komputasi
       - waktu komunikasi antar prosesor
    """
    n = len(tasks)
    if n == 0:
        return {}, 0.0

    # --- tabel biaya komputasi (anggap sama untuk semua prosesor) ---
    cost_table = [t["cost"] for t in tasks]

    # --- bangun struktur DAG: predecessor, successor, dan biaya komunikasi ---
    preds = {i: [] for i in range(n)}
    succs = {i: [] for i in range(n)}
    comm: Dict[Tuple[int, int], float] = {}

    for e in edges:
        s = e["src"]
        d = e["dst"]
        c = float(e.get("comm", 0.0) or 0.0)
        preds[d].append(s)
        succs[s].append(d)
        comm[(s, d)] = c

    # --- Tahap 1: hitung prioritas (upward rank) untuk setiap task ---
    memo_rank = {}
    rank_u = {
        i: compute_ranku(i, succs, cost_table, comm, memo_rank)
        for i in range(n)
    }

    # urutkan task berdasarkan rank_u menurun
    order = sorted(range(n), key=lambda t: rank_u[t], reverse=True)

    # --- Tahap 2: penjadwalan ke prosesor dengan EFT minimum ---
    proc_avail = [0.0] * processors  # kapan tiap prosesor ready
    AST = {i: 0.0 for i in range(n)}  # Actual Start Time tiap task
    AFT = {i: 0.0 for i in range(n)}  # Actual Finish Time tiap task
    assignment: Dict[int, int] = {}   # task -> prosesor

    for t in order:
        best_proc = 0
        best_finish = float("inf")
        best_start = 0.0

        # coba tempatkan task t di setiap prosesor
        for p in range(processors):
            # waktu siap dari sisi dependency
            ready_pred = 0.0
            for pred in preds[t]:
                pred_proc = assignment[pred]
                comm_time = comm.get((pred, t), 0.0) if pred_proc != p else 0.0
                ready_pred = max(ready_pred, AFT[pred] + comm_time)

            est = max(proc_avail[p], ready_pred)           # earliest start time
            eft = est + cost_table[t]                      # earliest finish time

            if eft < best_finish:
                best_finish = eft
                best_start = est
                best_proc = p

        # fix: assign task t ke prosesor terbaik
        assignment[t] = best_proc
        AST[t] = best_start
        AFT[t] = best_finish
        proc_avail[best_proc] = best_finish

    makespan = max(AFT.values()) if AFT else 0.0
    return assignment, makespan