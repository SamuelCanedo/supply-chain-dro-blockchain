# decision_engine.py

import os
from web3 import Web3

from dashboard.services.blockchain import get_status
from integration.send_to_chain import update_stock 
import numpy as np 
import pandas as pd

from pipeline.forecast_model import SupplyChainMVP
from pipeline.demand_simulator_v2 import generate_automotive_demand
from pipeline.dro_models.wasserstein_model import run_wasserstein
from pipeline.simulation_engine import compare_policies

from integration.orders.order_generator import generate_order
from integration.send_to_chain import send_decision 
from config import RPC_URL

import json 

w3 = Web3(Web3.HTTPProvider(RPC_URL))

def set_stock_directly(new_stock_level):
    """
    UPDATE stock directly on the blockchain without mathematical operations.
    This REPLACES the previous value completely.
    """
    status = get_status()
    current_stock = int(status['stock'])
    
    print(f"\n🔄 Updating stock:")
    print(f"   Previous stock: {current_stock}")
    print(f"   New stock: {new_stock_level}")
    print(f"   Change: {new_stock_level - current_stock}")
    
    # Send the new value directly to the blockchain
    tx = update_stock(new_stock_level)
    
    receipt = w3.eth.wait_for_transaction_receipt(tx)
    
    updated = get_status()
    print(f"✅ Stock updated: {updated['stock']}")
    
    return updated['stock']

def update_stock_simple(new_stock):
    """Update stock directly (replacement) without accumulation."""
    from integration.send_to_chain import update_stock
    update_stock(new_stock)
    print(f"Stock updated to: {new_stock}")

def save_metrics(metrics):
    path = "dashboard/data/metrics.json"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(metrics, f)

def run_decision(model_type="wasserstein"):
    print(f"\n🔄 Running Decision Engine | Model: {model_type}")
    
    #----------------------------------------------------
    # 1. GENERATE DEMAND
    #----------------------------------------------------
    seed_val = np.random.randint(0, 10000)
    df = generate_automotive_demand(180, seed=seed_val)
    df_model = df.rename(columns={"tier1": "demand"})
    print(f"✅ Demand generated with seed: {seed_val}")
    
    df_model = df.rename(columns={"tier1": "demand"})
    
    #----------------------------------------------------
    # 2. FORECAST
    #----------------------------------------------------
    model = SupplyChainMVP()
    data = model.prepare_data(df_model, target="demand")
    model.fit(data, target="demand")
    forecast = model.predict(30)
    
    #----------------------------------------------------
    # 3. DRO - Calculate optimal quantity
    #----------------------------------------------------
    demand_full = np.concatenate([
        df_model["demand"].values[-60:],
        forecast,
    ])
    
    result = run_wasserstein(df_model["demand"].values, forecast)
    
    Q_opt = result["Q_opt"]  # Optimal inventory quantity

    update_stock_simple(Q_opt)  # Update stock directly with the optimal quantity

    avg_demand = np.mean(df_model["demand"].values[-30:])
    new_reorder_point = max(20, int(avg_demand * 2))  # Example: 50% of average demand as new reorder point
    
    from dashboard.services.blockchain import set_reorder_point
    set_reorder_point(new_reorder_point)

    order = generate_order(Q_opt)

    risk = result.get("risk", 0)
    epsilon = result.get("epsilon", 0)
    
    print(f"\n📦 Optimal quantity calculated: {Q_opt}")
    print(f"⚠️ Risk: {risk}")
    print(f"ε Epsilon: {epsilon:.4f}")
    
    #----------------------------------------------------
    # 4. UPDATE STOCK DIRECTLY (NO ACCUMULATION)
    #----------------------------------------------------
    # The new stock IS the optimal quantity, not added or subtracted from the current stock. This is a direct replacement.
    new_stock = Q_opt
    
    # Update blockchain with the new value
    set_stock_directly(new_stock)
    
    #----------------------------------------------------
    # 5. KPIs
    #----------------------------------------------------
    metrics = compare_policies(
        demand=demand_full,
        dro_Q=Q_opt
    )
    
    save_metrics(metrics)
    
    print("\n📊 KPIs:")
    print(metrics)
    
    # ----------------------------------------------------------
    # 6. Keep history of epsilon for the dashboard
    # ----------------------------------------------------------
    
    epsilon_path = "dashboard/data/epsilon_history.json"
    os.makedirs("dashboard/data", exist_ok=True)

    history = []
    if os.path.exists(epsilon_path):
        with open(epsilon_path, "r") as f:
            history = json.load(f)
    
    history.append({
        "timestamp": pd.Timestamp.now().isoformat(),
        "epsilon": float(epsilon)
    })

    # keep only the last 100 entries to avoid file bloat
    if len(history) > 100:
        history = history[-100:]

    with open(epsilon_path, "w") as f:
        json.dump(history, f)

    # ----------------------------------------------------------
    # 6.1. Save complete history of metrics for the dashboard
    # ----------------------------------------------------------
    
    metrics_path = "dashboard/data/metrics_history.json"
    metrics_history = []
    if os.path.exists(metrics_path):
        with open(metrics_path, "r") as f:
            metrics_history = json.load(f)
    
    metrics_with_time = metrics.copy()
    metrics_with_time["timestamp"] = pd.Timestamp.now().isoformat()
    metrics_with_time["Q_opt"] = int(Q_opt)
    metrics_with_time["epsilon"] = float(epsilon)
    metrics_with_time["risk"] = float(risk)
    metrics_with_time["model"] = model_type
    metrics_with_time["savings_usd"] = float(metrics.get("savings_usd", 0))
    metrics_with_time["cvar_savings"] = float(metrics.get("cvar_savings", 0))

    metrics_history.append(metrics_with_time)

    if len(metrics_history) > 1000:
        metrics_history = metrics_history[-1000:]
        
    with open(metrics_path, "w") as f:
        json.dump(metrics_history, f)
    
    #----------------------------------------------------
    # 7. GENERATE ORDER (record the decision, simulate user action)
    #----------------------------------------------------
    order = generate_order(Q_opt)
    if order:
        print(f"✅ Order generated: {order['order_id']}")
    
    #----------------------------------------------------
    # 8. SEND DECISION TO BLOCKCHAIN
    #----------------------------------------------------
    forecast_total = float(np.sum(forecast))
    
    send_decision(
        forecast_total,
        Q_opt,
        risk,
    )
    
    print("✅ Decision sent to Blockchain")
    
    return {
        "forecast": forecast_total,
        "Q_opt": Q_opt,
        "risk": risk,
        "epsilon": epsilon,
        "model": model_type,
        "metrics": metrics
    }
