## charts.py

import streamlit as st
import pandas as pd
import os 
import json

def load_stock_history():
    """Load stock history from a file"""
    history_path = "dashboard/data/stock_history.json"
    if not os.path.exists(history_path):
        return []
    with open(history_path, "r") as f:
        return json.load(f)

def save_stock_history(stock, reorder_point):
    """Save the current stock to the history"""
    history_path = "dashboard/data/stock_history.json"
    os.makedirs(os.path.dirname(history_path), exist_ok=True)
    
    history = load_stock_history()
    history.append({
        "timestamp": pd.Timestamp.now().isoformat(),
        "stock": stock,
        "reorder_point": reorder_point
    })
    
    # keep only the last 100 entries to avoid file bloat
    if len(history) > 100:
        history = history[-100:]
    
    with open(history_path, "w") as f:
        json.dump(history, f)

def render_stock_chart(status):
    st.subheader("📈 Stock Evolution")

    if "error" in status:
        st.error("Blockchain not connected")
        return

    current_stock = status.get('stock', 0)
    reorder_point = status.get('reorder_point', 0)
    
    # Save current state to history
    save_stock_history(current_stock, reorder_point)
    
    # Load history for plotting
    history = load_stock_history()
    
    if len(history) < 2:
        st.info("Accumulating historical data...")
        # Show only current point
        df = pd.DataFrame({
            'timestamp': [pd.Timestamp.now()],
            'stock': [current_stock],
            'reorder_point': [reorder_point]
        })
        chart_df = df.set_index('timestamp')[['stock', 'reorder_point']]
        st.line_chart(chart_df)
    else:
        # Show full history
        df = pd.DataFrame(history)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        chart_df = df.set_index('timestamp')[['stock', 'reorder_point']]
        st.line_chart(chart_df)
    
    col1, col2 = st.columns(2)
    col1.metric("Current Stock", f"{current_stock:,}")
    col2.metric("Reorder Point", f"{reorder_point:,}")

def render_epsilon_chart(epsilon_history):
    df = pd.DataFrame(epsilon_history)
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["timestamp"])
    st.subheader("MODEL CONFIDENCE (EPSILON)")
    st.line_chart(df.set_index("timestamp")["epsilon"])

def render_policy_gap(Q_dro, Q_baseline):
    df = pd.DataFrame({
        "Policy": ["Baseline", "DRO"],
        "Q_value": [Q_baseline, Q_dro]
    })
    st.subheader("POLICY COMPARISON")
    st.bar_chart(df.set_index("Policy"))

def render_kpi_comparison(metrics):
    df = pd.DataFrame({
        "Metrics": ["Savings", "Stockouts Reduction", "CVaR Protection"],
        "Value": [
            metrics.get("savings_pct", 0), 
            metrics.get("stockouts_reduction_pct", 0), 
            metrics.get("cvar_savings", 0)
        ]
    })
    st.bar_chart(df.set_index("Metrics"))