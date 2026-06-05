import streamlit as st
import json
import os

st.title("Liverpool Pulse")

DATA_FILE = "data.json"
LATEST_FILE = "latest_post.json"


def load_json(path):
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except:
            return None
    return None


data = load_json(DATA_FILE) or []
latest = load_json(LATEST_FILE)

liverpool_data = [row for row in data if row["team"] == "Liverpool"]

# ---------------- METRICS ----------------
if liverpool_data:
    latest_row = liverpool_data[-1]

    st.metric("Sentiment Score", f"{latest_row['sentiment']:.1f}")
    st.metric("Mentions (Last Hour)", latest_row["mentions"])
else:
    st.info("Waiting for first Liverpool data run...")


# ---------------- LATEST POST ----------------
if latest:
    st.subheader("Latest Post")
    st.write(latest.get("text", "N/A"))

    st.subheader("Latest Post Sentiment")
    st.write(f"{latest.get('score', 0):.1f} / 100")
