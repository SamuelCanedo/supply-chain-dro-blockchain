## orders.py

import streamlit as st
import pandas as pd 

def render_orders(orders):
    st.subheader("Orders")

    if not orders:
        st.warning("No orders found")
        return
    
    df = pd.DataFrame(orders)
    df = df.sort_values("timestamp", ascending=False)

    st.dataframe(df.head(10), use_container_width=True)