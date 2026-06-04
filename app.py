import json
import os

def load_latest_post():
    if os.path.exists("latest_post.json"):
        with open("latest_post.json", "r") as f:
            return json.load(f)
    return None


latest = load_latest_post()

if latest:
    st.subheader("Latest Post")
    st.write(latest["text"])

    st.subheader("Latest Post Sentiment")
    st.write(f"{latest['score']:.1f} / 100")
