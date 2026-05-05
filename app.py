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

    st.subheader("Sentiment (24h)")
    st.line_chart(data.set_index("timestamp")[["sentiment"]])

    st.subheader("Mentions (24h)")
    st.line_chart(data.set_index("timestamp")[["mentions"]])

import requests
from bs4 import BeautifulSoup
from sentiment import score_text
from db import save_row

HEADERS = {"User-Agent": "Mozilla/5.0"}

KEYWORDS = {
    "Timberwolves": [
        "Minnesota Timberwolves", "Anthony Edwards", "Gobert", "Timberwolves"
    ],
    "Wild": [
        "Minnesota Wild", "Kaprizov", "Boldy", "Wild NHL"
    ]
}

def fetch_x_posts(keyword):
    url = f"https://nitter.net/search?f=tweets&q={keyword.replace(' ', '%20')}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        tweets = soup.find_all("div", class_="tweet-content")
        return [t.get_text(strip=True) for t in tweets[:20]]
    except:
        return []

def fetch_all(team):
    posts = []
    for kw in KEYWORDS[team]:
        posts += fetch_x_posts(kw)
    return posts

def run(team):
    posts = fetch_all(team)

    if not posts:
        save_row(team, 50, 0)
        return

    scores = [score_text(p) for p in posts]
    avg = sum(scores) / len(scores)

    save_row(team, avg, len(posts))

if __name__ == "__main__":
    import sys
    run(sys.argv[1])

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

analyzer = SentimentIntensityAnalyzer()

def score_text(text):
    score = analyzer.polarity_scores(text)["compound"]
    return (score + 1) * 50

import sqlite3
import pandas as pd
from datetime import datetime

conn = sqlite3.connect("pulse.db", check_same_thread=False)

conn.execute("""
CREATE TABLE IF NOT EXISTS sentiment (
team TEXT,
timestamp TEXT,
sentiment REAL,
mentions INTEGER
)
""")

def save_row(team, sentiment, mentions):
    conn.execute(
        "INSERT INTO sentiment VALUES (?, ?, ?, ?)",
        (team, datetime.utcnow(), sentiment, mentions)
    )
    conn.commit()

def get_data(team):
    df = pd.read_sql_query(
        "SELECT * FROM sentiment WHERE team=? ORDER BY timestamp",
        conn,
        params=(team,)
    )
    return df

streamlit
pandas
requests
beautifulsoup4
vaderSentiment

[theme]
base="dark"

name: hourly-run

on:
  schedule:
    - cron: "0 * * * *"
  workflow_dispatch:

jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - run: pip install -r requirements.txt
      - run: python collector.py Timberwolves
      - run: python collector.py Wild
