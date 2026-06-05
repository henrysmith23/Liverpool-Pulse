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
LATEST_POST_FILE = "latest_post.json"


# ---------------- HELPERS ----------------
def load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except:
            return default
    return default


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f)


# ---------------- SCRAPE ----------------
def get_last_page_number():
    res = requests.get(THREAD_URL, headers=HEADERS, timeout=15)
    soup = BeautifulSoup(res.text, "html.parser")

    pagination = soup.find("ul", class_="ui-pagination")
    if not pagination:
        return 1

    page_links = pagination.find_all("a")
    max_page = 1
    for link in page_links:
        try:
            num = int(link.get_text(strip=True))
            if num > max_page:
                max_page = num
        except ValueError:
            continue

    return max_page


def fetch_posts():
    last_page = get_last_page_number()
    url = f"{THREAD_URL}?page={last_page}"
    print(f"Fetching page {last_page}: {url}")

    res = requests.get(url, headers=HEADERS, timeout=15)
    soup = BeautifulSoup(res.text, "html.parser")

    posts = []

    for article in soup.find_all("article"):
        try:
            wrapper = article.find_parent("td")

            if not wrapper:
                continue

            post_id_raw = wrapper.get("id", "")
            post_id = post_id_raw.replace("post-", "") if "post-" in post_id_raw else None

            msg = article.find("div", class_="message")
            if not msg:
                continue
            text = msg.get_text(strip=True)

            ts_tag = article.find("abbr", class_="o-timestamp")
            if not ts_tag:
                continue

            timestamp = int(ts_tag.get("data-timestamp", 0))

            if post_id and timestamp and text:
                posts.append({
                    "id": str(post_id),
                    "timestamp": timestamp,
                    "text": text
                })

        except Exception as e:
            continue

    return posts


# ---------------- RUN ----------------
def run():

    posts = fetch_posts()

    print("TOTAL POSTS FOUND:", len(posts))

    seen = set(load_json(SEEN_FILE, []))
    last_run = load_json(LAST_RUN_FILE, 0)

    # FIX: normalize timestamp to ms
    if last_run < 10**12:
        last_run = last_run * 1000

    new_posts = [
        p for p in posts
        if p["id"] not in seen and int(p["timestamp"]) > int(last_run)
    ]

    print("NEW POSTS FOUND:", len(new_posts))

    # ALWAYS update last run time even if empty
    now_ts = int(datetime.utcnow().timestamp() * 1000)

    if not new_posts:
        save_row("Liverpool", 50, 0)
        save_json(LAST_RUN_FILE, now_ts)
        return

    # sentiment calculation
    scores = [score_text(p["text"]) for p in new_posts]
    avg = sum(scores) / len(scores)

    latest = max(new_posts, key=lambda x: x["timestamp"])

    # update tracking
    seen.update([p["id"] for p in new_posts])

    save_json(SEEN_FILE, list(seen))
    save_json(LAST_RUN_FILE, now_ts)

    save_row("Liverpool", avg, len(new_posts))

    # ALWAYS create latest post file
    save_json(LATEST_POST_FILE, {
        "text": latest["text"],
        "score": score_text(latest["text"]),
        "timestamp": latest["timestamp"]
    })


if __name__ == "__main__":
    run()
