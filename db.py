import pandas as pd
from datetime import datetime
import os

FILE = "pulse.csv"

def save_row(team, sentiment, mentions):
    row = pd.DataFrame([{
        "team": team,
        "timestamp": datetime.utcnow(),
        "sentiment": sentiment,
        "mentions": mentions
    }])

    if os.path.exists(FILE):
        df = pd.read_csv(FILE)
        df = pd.concat([df, row], ignore_index=True)
    else:
        df = row

    df.to_csv(FILE, index=False)


def get_data(team):
    if not os.path.exists(FILE):
        return pd.DataFrame()

    df = pd.read_csv(FILE)
    df = df[df["team"] == team]
    return df
