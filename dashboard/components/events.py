## events.py

import streamlit as st
import pandas as pd

def render_events(events):
    st.subheader("Event Feed")

    if not events:
        st.info("No events to display.")
        return
    
    df = pd.DataFrame(events)

    if "timestamp" in df.columns:
        df = df.sort_values("timestamp", ascending=False)

    for _, row in df.head(10).iterrows():
        st.text(f"[{row.get('timestamp', '?')}] {row.get('event', '?')} -> {row.get('details', '')}")