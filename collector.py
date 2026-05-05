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
