## health.py

import streamlit as st

def render_health(status):
    st.subheader("🚦 System Health")

    if "error" in status:
        st.error(f"XX {status['error']}")

    if "error" in status:
        st.error("Blockchain not available")
        return
    
    stock = status.get("stock", 0)

    reorder = status.get("reorder_point", 0)

    ratio = stock / reorder if reorder > 0 else 0

    if ratio > 1.5:
        st.success("All Good")
    elif ratio > 1.0:
        st.warning("Low Stock")
    else:
        st.error("Critical Stock Level")
    
    st.progress(min(ratio / 2, 1.0))