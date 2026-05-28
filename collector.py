import requests
from bs4 import BeautifulSoup
from sentiment import score_text
from db import save_row

HEADERS = {"User-Agent": "Mozilla/5.0"}

# ---------- TIMBERWOLVES (AIRBNB LINK) ----------
def fetch_wolves():
    posts = []

    try:
        url = "https://www.airbnb.com/l/JqUALnWT?s=67&unique_share_id=fdf59037-3af0-4290-a266-28a2785a0e18"

        res = requests.get(url, headers=HEADERS, timeout=15)

        soup = BeautifulSoup(res.text, "html.parser")

        text = soup.get_text(" ", strip=True)

        posts.append(text[:5000])

    except Exception as e:
        print("wolves source failed:", e)

    return posts


# ---------- WILD (FORUM) ----------
def fetch_wild():
    posts = []

    try:
        url = "https://hockeywilderness.com/forums/forum/2-minnesota-wild-talk/"

        res = requests.get(url, headers=HEADERS, timeout=15)

        soup = BeautifulSoup(res.text, "html.parser")

        titles = soup.find_all(["h2", "h3", "a"])

        for t in titles[:40]:
            txt = t.get_text(strip=True)

            if len(txt) > 10:
                posts.append(txt)

    except Exception as e:
        print("wild source failed:", e)

    return posts


# ---------- RUN ----------
def run(team):

    if team == "Timberwolves":
        posts = fetch_wolves()

    elif team == "Wild":
        posts = fetch_wild()

    else:
        posts = []

    print("POST COUNT:", len(posts))

    if len(posts) == 0:
        save_row(team, 50, 0)
        return

    scores = [score_text(p) for p in posts]

    avg = sum(scores) / len(scores)

    save_row(team, avg, len(posts))


if __name__ == "__main__":
    import sys
    run(sys.argv[1])
