import streamlit as st
import json
import os

def load_latest_post():
    if os.path.exists("latest_post.json"):
        with open("latest_post.json", "r") as f:
            return json.load(f)
    return None


latest = load_latest_post()

if latest and isinstance(latest, dict):
    st.subheader("Latest Post")

    st.write(latest.get("text", "No text available"))

    st.subheader("Latest Post Sentiment")

    score = latest.get("score", None)

    if score is not None:
        st.write(f"{float(score):.1f} / 100")
    else:
        st.write("No sentiment score available")
else:
    st.info("Waiting for first Liverpool data run...")
