## reorder_monitor.py

import streamlit as st

def render_reorder_monitor(status):
    st.caption(f"🎯 Current reorder point: **{status['reorder_point']}**")
    if status['stock'] < status['reorder_point']:
        st.warning("Stock below reorder point! Consider placing an order.")