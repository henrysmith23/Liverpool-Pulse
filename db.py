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
