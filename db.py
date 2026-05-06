import json
import pandas as pd
from datetime import datetime
import os

FILE = "data.json"

def save_row(team, sentiment, mentions):

    row = {
        "team": team,
        "timestamp": datetime.utcnow().isoformat(),
        "sentiment": sentiment,
        "mentions": mentions
    }

    if os.path.exists(FILE):
        with open(FILE, "r") as f:
            data = json.load(f)
    else:
        data = []

    data.append(row)

    with open(FILE, "w") as f:
        json.dump(data, f)

def get_data(team):
    if not os.path.exists(FILE):
        return pd.DataFrame()

    with open(FILE, "r") as f:
        data = json.load(f)

    df = pd.DataFrame(data)
    df = df[df["team"] == team]

    return df
