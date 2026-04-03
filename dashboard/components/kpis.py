## kpis.py

import streamlit as st
    
def render_kpis(status):
    if "error" in status:
        st.error(status['error'])
        return
    
    stock = status.get("stock", 0)
    reorder = status.get("reorder_point", 0)
    last_order = status.get("last_order", 0)
    shortage = status.get("shortage", False)

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Stock", stock)
    col2.metric("Reorder Point", reorder)
    col3.metric("Last Order", last_order)

    if shortage:
        state = "⚠️ Shortage"
    elif stock < reorder * 1.2:
        state = "⚠️ Low Stock"
    else:
        state = "All Good"
    
    col4.metric("System State", state)

def render_advanced_kpis(metrics):
    if not metrics:
        st.info("No metrics available")
        return
    
    col1, col2, col3 = st.columns(3)

    savings_pct = metrics.get("savings_pct", 0)
    savings_usd = metrics.get("savings_usd", 0)

    col1.metric(
        "Savings vs Baseline",
        f"{savings_pct}%" if savings_pct else "0%",
        delta=f"${savings_usd:,.0f}" if savings_usd else None
    )

    stockout_reduction = metrics.get("stockouts_reduction", 0)
    col2.metric(
        "Stockout Reduction",
        f"{stockout_reduction:.1f}%" if stockout_reduction else "0%"
    )
    
    cvar_savings = metrics.get("cvar_savings", 0)
    col3.metric(
        "🛡️ CVaR Protection",
        f"{cvar_savings}%" if cvar_savings else "0%"
    )