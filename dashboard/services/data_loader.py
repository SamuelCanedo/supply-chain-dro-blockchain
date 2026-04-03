## data_loader.py

import os
import json
import streamlit as st
from integration.orders.order_generator import get_recent_orders

def load_orders(n=20):
    return get_recent_orders(n)

def load_events():
    events_path = "dashboard/data/events.json"
    if not os.path.exists(events_path):
        return []
    with open(events_path, "r") as f:
        return json.load(f)

@st.cache_data(ttl=1)
def load_metrics():
    metrics_path = "dashboard/data/metrics.json"
    if not os.path.exists(metrics_path):
        return {}
    try:
        with open(metrics_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}