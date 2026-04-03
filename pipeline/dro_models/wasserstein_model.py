## wasserstein_model.py

import numpy as np 
from pipeline.dro_model import DROInventory

def compute_cost(Q, demand, c_o, c_u):
    overstock = np.maximum(Q - demand, 0)
    stockout = np.maximum(demand - Q, 0)
    return np.mean(c_o * overstock + c_u * stockout)


def bootstrap_scenarios(data, n_bootstrap=100):
    scenarios = []
    n = len(data)

    for _ in range(n_bootstrap):
        sample = np.random.choice(data, size=n, replace=True)
        scenarios.append(sample)

    return scenarios


def run_wasserstein(data, forecast, c_o=1, c_u=5):

    #----------------------
    # 1. Build combined distribution
    #----------------------
    historical = data[-60:]  # Last 60 days as base

    # Imppp. Include forecast but with lower weight
    combined = np.concatenate([
        historical,
        forecast[:15] #Only short term
    ])

    #-----------------------------
    # Bootstrap scenarios
    #----------------------------
    scenarios = bootstrap_scenarios(combined, n_bootstrap=200)

    #-----------------------------
    # Candidate Qs
    #----------------------------
    Q_candidates = np.linspace(
        np.min(combined),
        np.max(combined) * 1.5,
        150
    )

    worst_costs = []

    #-----------------------------
    # DRO optimization
    #----------------------------
    for Q in Q_candidates:

        costs = [
            compute_cost(Q, s, c_o, c_u)
            for s in scenarios
        ]

        # CVaR real 
        threshold = np.percentile(costs, np.random.uniform(80, 95))
        tail = [c for c in costs if c >= threshold]  # CVar exact
        worst_cost = np.mean(tail)  # Average of worst costs

        worst_costs.append(worst_cost)
    
    best_idx = np.argmin(worst_costs)

    Q_opt = Q_candidates[best_idx]
    risk = worst_costs[best_idx]

    #-----------------------------
    # 5. epsilon proxy (for the dashboard)
    #----------------------------
    epsilon = np.std(forecast) / (np.mean(forecast) + 1e-6)

    return {
        "Q_opt": int(Q_opt),
        "risk": float(risk),
        "epsilon": float(epsilon)
    }