## exporter.py

import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

def export_to_excel():
    "Export all historical data to Excel"

    # Load all historical data
    # The metrics.json file contains the latest metrics, but we want the full history for export, which is stored in metrics_history.json.
    # We also want the epsilon history and stock history for a complete export. Finally, we will include recent orders for context.
    
    data = {
        "metrics_history": [],
        "epsilon_history": [],
        "stock_history": [],
        "orders": [],
    }

    # Load historical metrics
    metrics_path = "dashboard/data/metrics_history.json"
    if os.path.exists(metrics_path):
        with open(metrics_path, "r") as f:
            data["metrics_history"] = json.load(f)

    # Load epsilon history
    epsilon_path = "dashboard/data/epsilon_history.json"
    if os.path.exists(epsilon_path):
        with open(epsilon_path, "r") as f:
            data["epsilon_history"] = json.load(f)

    # Load stock history
    stock_path = "dashboard/data/stock_history.json"
    if os.path.exists(stock_path):
        with open(stock_path, "r") as f:
            data["stock_history"] = json.load(f)

    # Load orders
    from integration.orders.order_generator import get_recent_orders
    data["orders"] = get_recent_orders(100)  # Load up to 100 recent orders

    # Create an Excel with multiple sheets
    output_path = f"dashboard/exports/export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    os.makedirs("dashboard/exports", exist_ok=True)
    
    with pd.ExcelWriter(output_path, engine="xlsxwriter") as writer:

        # Metrics sheet
        if data["metrics_history"]:
            df_metrics = pd.DataFrame(data["metrics_history"])
            df_metrics.to_excel(writer, sheet_name="Metrics", index=False)

        # epsilon history sheet
        if data["epsilon_history"]:
            df_epsilon = pd.DataFrame(data["epsilon_history"])
            df_epsilon["timestamp"] = pd.to_datetime(df_epsilon["timestamp"])
            df_epsilon.to_excel(writer, sheet_name="Epsilon History", index=False)
        
        # stock history sheet
        if data["stock_history"]:
            df_stock = pd.DataFrame(data["stock_history"])
            df_stock["timestamp"] = pd.to_datetime(df_stock["timestamp"])
            df_stock.to_excel(writer, sheet_name="Stock History", index=False)
        
        # orders sheet
        if data["orders"]:
            df_orders = pd.DataFrame(data["orders"])
            df_orders["timestamp"] = pd.to_datetime(df_orders["timestamp"])
            df_orders.to_excel(writer, sheet_name="Orders", index=False)

        # statistical summary sheet
        summary_data = create_summary(data)
        df_summary = pd.DataFrame([summary_data])
        df_summary.to_excel(writer, sheet_name="Summary", index=False)

    return output_path

def create_summary(data):
    """Create a summary of key statistics for the summary sheet"""
    summary = {
        "export_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_cycles": len(data["metrics_history"]),
        "total_orders": len(data["orders"]),
        "average_epsilon": pd.DataFrame(data["epsilon_history"])["epsilon"].mean() if data["epsilon_history"] else None,
        "avg_savings": pd.DataFrame(data["metrics_history"])["savings_usd"].mean() if data["metrics_history"] else None,
        "total_savings_usd": pd.DataFrame(data["metrics_history"])["savings_usd"].sum() if data["metrics_history"] else None,
        "avg_cvar_savings": pd.DataFrame(data["metrics_history"])["cvar_savings"].mean() if data["metrics_history"] else None,
        "average_stock": pd.DataFrame(data["stock_history"])["stock"].mean() if data["stock_history"] else None,
        "min_stock": pd.DataFrame(data["stock_history"])["stock"].min() if data["stock_history"] else None,
        "max_stock": pd.DataFrame(data["stock_history"])["stock"].max() if data["stock_history"] else None
    }

    return summary

def render_export_button():
    "Render a button in the Streamlit app to trigger the export"
    st.subheader("Export Data")

    col1 = st.columns(1)[0]

    with col1:
        if st.button("Export to Excel", type="primary"):
            with st.spinner("Exporting data..."):
                try:
                    file_path = export_to_excel()
                    with open(file_path, "rb") as f:
                        st.download_button(
                            label="Download Excel File",
                            data=f,
                            file_name=file_path.split("/")[-1],
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    st.success(f"Data exported successfully: {file_path}")
                except Exception as e:
                    st.error(f"Failed to export data: {e}")