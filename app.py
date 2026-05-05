import streamlit as st
import pandas as pd
from db import get_data

st.set_page_config(page_title="Wild/Wolves Pulse", layout="wide")

st.title("Wild/Wolves Pulse")

team = st.radio("Select Team", ["Timberwolves", "Wild"])

data = get_data(team)

if data.empty:
    st.warning("No data yet. Wait for first hourly run.")
else:
    st.metric("Current Sentiment (0-100)", round(data["sentiment"].iloc[-1], 1))
    st.metric("Mentions (Last Hour)", int(data["mentions"].iloc[-1]))

    st.subheader("Sentiment")
    st.line_chart(data.set_index("timestamp")[["sentiment"]])

    st.subheader("Mentions")
    st.line_chart(data.set_index("timestamp")[["mentions"]])
