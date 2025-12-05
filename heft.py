# heft.py
def compute_ranku(task, adj, cost_table, memo):
    if task in memo:
        return memo[task]
    if not adj[task]:
        memo[task] = cost_table[task]
    else:
        memo[task] = cost_table[task] + max(
            compute_ranku(child, adj, cost_table, memo) for child in adj[task]
        )
    return memo[task]


def heft_schedule(tasks, edges, processors=4):
    cost_table = {t["task"]: t["cost"] for t in tasks}

    # adjacency list
    adj = {t["task"]: [] for t in tasks}
    for e in edges:
        adj[e["src"]].append(e["dst"])

    # compute ranku
    memo = {}
    order = sorted(cost_table.keys(),
                   key=lambda t: compute_ranku(t, adj, cost_table, memo),
                   reverse=True)

    # schedule
    proc_load = [0] * processors
    schedule = {}

    for t in order:
        p = min(range(processors), key=lambda x: proc_load[x])
        schedule[t] = p
        proc_load[p] += cost_table[t]

    makespan = max(proc_load)
    return schedule, makespan