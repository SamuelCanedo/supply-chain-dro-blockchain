# simulation_engine.py

import numpy as np 

# Base simulation (With reorder + lead time)

def simulate_inventory(
    demand,
    Q,
    reorder_point=None,
    lead_time=3,
    c_h=1,
    c_s=10
):
    """
    Simulate inventory system with (s, Q) policy

    demand: array of demand
    Q: order quantity
    reorder_point: reorder point (if none = Q * 0.4)
    lead_time: order lead time in days
    c_h: holding cost
    c_s: stockout cost
    """

    if reorder_point is None:
        reorder_point = Q * 0.4  # Reorder when stock falls below 40% of Q

    stock = Q  # Initial inventory
    pipeline_orders = []  # Orders in transit
    stockouts = 0
    total_cost = 0
    daily_costs = []

    for t in range(len(demand)):
        d = demand[t]

        #-----------------------------------------------
        # 1. Orders arrive
        #-----------------------------------------------
        arriving = [o for o in pipeline_orders if o["arrival"] == t]
        for o in arriving:
            stock += o["qty"]

        pipeline_orders = [o for o in pipeline_orders if o["arrival"] > t]        
        
        #-----------------------------------------------
        # 2. Satisfy demand
        #-----------------------------------------------
        if d > stock:
            shortage = d - stock
            stockouts += 1
            cost = shortage * c_s  # Stockout cost
            stock = 0
        else:
            holding = stock - d

            cost = holding * c_h  # Holding cost
            stock -= d

        total_cost += cost
        daily_costs.append(cost)

        #-----------------------------------------------
        # 3. Reorder
        #-----------------------------------------------
        has_pending = len(pipeline_orders) > 0

        if stock <= reorder_point and not has_pending:
            pipeline_orders.append({
                "qty": Q,
                "arrival": t + lead_time
            })  # Order arrives in lead_time days

    return {
        "total_cost": total_cost,
        "stockouts": stockouts,
        "daily_costs": np.array(daily_costs)
    }

#-----------------------------------------------
# 2. CVaR (TAIL RISK) CALCULATION
#-----------------------------------------------

def compute_cvar(costs, alpha=0.9):
    """
    Calculate CVaR (Conditional Value at Risk) for a series of costs.

    costs: array of daily costs
    alpha: confidence level (e.g. 0.90 for the worst 10%)
    """
    threshold = np.quantile(costs, alpha)
    tail = costs[costs >= threshold]

    return np.mean(tail) if len(tail) > 0 else 0

#-----------------------------------------------
# 3. Policy comparison
#-----------------------------------------------

def compare_policies(
    demand,
    dro_Q,
    baseline_quantile=0.65,
    lead_time= np.random.randint(2, 6),
    epsilon=None
):
    """
    Compare two inventory policies (baseline and DRO) in terms of costs and CVaR.

    demand: array of demand
    dro_Q: order quantity for the DRO policy
    baseline_quantile: quantile to determine Q_baseline
    lead_time: order lead time in days
    """

    # Baseline policy 
    baseline_Q = np.quantile(demand, baseline_quantile)  # E.g. 65% of historical demand

    # Simulations
    baseline = simulate_inventory(
        demand,
        Q=baseline_Q,
        lead_time=lead_time,
        c_s=10
    )

    dro = simulate_inventory(
        demand,
        Q=dro_Q,
        lead_time=lead_time,
        c_s=10
    )   

    # CVaR
    baseline_cvar = compute_cvar(baseline["daily_costs"])
    dro_cvar = compute_cvar(dro["daily_costs"])

    # KPIs 
    savings = baseline["total_cost"] - dro["total_cost"]

    ## Safe division
    stockout_reduction = 0
    if baseline["stockouts"] > 0:
        stockout_reduction = (
            (baseline["stockouts"] - dro["stockouts"]) 
            / baseline["stockouts"]
        ) * 100 

    metrics = {
        "baseline_Q": int(baseline_Q),
        "dro_Q": int(dro_Q),
        "epsilon": epsilon if epsilon is not None else 0,

        "savings_pct": float(round(
           (savings / baseline["total_cost"]) * 100, 2
        )),

        "savings_usd": int(savings),

        "stockouts_reduction": float(round(stockout_reduction, 2)),

        "baseline_stockouts": int(baseline["stockouts"]),
        "dro_stockouts": int(dro["stockouts"]),

        "cvar_baseline": int(baseline_cvar),
        "cvar_dro": int(dro_cvar),

        "cvar_savings": int(baseline_cvar - dro_cvar)
    }

    return metrics
