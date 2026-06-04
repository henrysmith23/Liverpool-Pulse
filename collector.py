import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
from sentiment import score_text
from db import save_row

HEADERS = {"User-Agent": "Mozilla/5.0"}

THREAD_URL = "https://anfield.freeforums.net/thread/755/liverpool-season-iraola-officially-confirmed"

SEEN_FILE = "seen_posts.json"
LAST_RUN_FILE = "last_run.json"


# ---------------- LOAD HELPERS ----------------
def load_json(path, default):
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return default


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f)


# ---------------- SCRAPE ----------------
def fetch_posts():
    res = requests.get(THREAD_URL, headers=HEADERS, timeout=15)
    soup = BeautifulSoup(res.text, "html.parser")

    posts = []

    for article in soup.find_all("article"):
        try:
            post_id_tag = article.find_parent("td")
            post_div = article.find("div", class_="message")

            if not post_div:
                continue

            text = post_div.get_text(strip=True)

            wrapper = article.find_parent("td")
            post_id = wrapper.get("id", "")
            post_id = post_id.replace("post-", "") if "post-" in post_id else None

            timestamp_tag = article.find("abbr", class_="o-timestamp")
            timestamp = int(timestamp_tag["data-timestamp"]) if timestamp_tag else None

            if post_id and timestamp and text:
                posts.append({
                    "id": post_id,
                    "timestamp": timestamp,
                    "text": text
                })

        except:
            continue

    return posts


# ---------------- RUN ----------------
def run():
    posts = fetch_posts()

    seen = set(load_json(SEEN_FILE, []))
    last_run = load_json(LAST_RUN_FILE, 0)

    new_posts = [
        p for p in posts
        if p["id"] not in seen and p["timestamp"] > last_run
    ]

    print("TOTAL POSTS:", len(posts))
    print("NEW POSTS:", len(new_posts))

    if not new_posts:
        save_row("Liverpool", 50, 0)
        return

    scores = [score_text(p["text"]) for p in new_posts]
    avg = sum(scores) / len(scores)

    latest = max(new_posts, key=lambda x: x["timestamp"])

    # update tracking
    seen.update([p["id"] for p in new_posts])
    save_json(SEEN_FILE, list(seen))
    save_json(LAST_RUN_FILE, max(p["timestamp"] for p in new_posts))

    save_row("Liverpool", avg, len(new_posts))

    # store latest post for dashboard
    save_json("latest_post.json", {
        "text": latest["text"],
        "score": score_text(latest["text"]),
        "timestamp": latest["timestamp"]
    })


if __name__ == "__main__":
    run()
