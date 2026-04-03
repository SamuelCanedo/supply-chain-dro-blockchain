## app.py

import streamlit as st
import os
import sys

from streamlit_autorefresh import st_autorefresh

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.blockchain import get_status
from services.data_loader import load_orders, load_events, load_metrics

from components.kpis import render_kpis, render_advanced_kpis
from components.charts import render_stock_chart
from components.orders import render_orders
from components.events import render_events
from components.health import render_health

## Configuration

st.set_page_config(layout="wide")

st.title("🧠 Supply Chain Control Tower (DRO + Blockchain)")

## Auto-refresh every REFRESH_RATE seconds

st_autorefresh(interval=2000, key="datarefresh") # 2 seconds

# -----------------------------
# DATA (UPDATED ON EACH REFRESH)
# -----------------------------

status = get_status()
orders = load_orders(20)
events = load_events()
metrics = load_metrics()

# -----------------------------
# KPIS
# -----------------------------

render_kpis(status)
render_advanced_kpis(metrics)

st.divider()

from components.reorder_monitor import render_reorder_monitor

render_reorder_monitor(status)

st.divider()

# -----------------------------
# MAIN GRID 
# -----------------------------
col1, col2 = st.columns([2, 1])

with col1:
    render_stock_chart(status, orders)

with col2:
    render_health(status)
    
st.divider()

col3, col4 = st.columns(2)

with col3:
    render_orders(orders)

with col4:
    render_events(events)