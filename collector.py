import requests
from bs4 import BeautifulSoup
from sentiment import score_text
from db import save_row

HEADERS = {"User-Agent": "Mozilla/5.0"}

KEYWORDS = {
    "Timberwolves": ["Minnesota Timberwolves", "Anthony Edwards", "Gobert"],
    "Wild": ["Minnesota Wild", "Kaprizov", "Boldy"]
}

RSS_FEEDS = {
    "Timberwolves": "https://www.espn.com/espn/rss/nba/news",
    "Wild": "https://www.espn.com/espn/rss/nhl/news"
}

# ---------- X SCRAPE ----------
def fetch_x_posts(keyword):
    try:
        url = f"https://nitter.net/search?f=tweets&q={keyword.replace(' ', '%20')}"
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        tweets = soup.find_all("div", class_="tweet-content")
        return [t.get_text(strip=True) for t in tweets[:15]]
    except:
        return []

# ---------- RSS NEWS ----------
def fetch_rss(team):
    try:
        url = RSS_FEEDS[team]
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.content, "xml")
        items = soup.find_all("item")
        return [i.title.text for i in items[:15]]
    except:
        return []

# ---------- REDDIT (no API) ----------
def fetch_reddit_scrape(team):
    try:
        url = f"https://www.reddit.com/r/{'nba' if team=='Timberwolves' else 'wildhockey'}/hot.json"
        res = requests.get(url, headers=HEADERS, timeout=10)
        data = res.json()
        return [
            c["data"]["title"]
            for c in data["data"]["children"][:15]
        ]
    except:
        return []

# ---------- COMBINE ----------
def fetch_all(team):
    posts = []

    try:
        url = RSS_FEEDS[team]
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.content, "xml")
        items = soup.find_all("item")

        for i in items[:30]:
            title = i.title.text
            if any(k.lower() in title.lower() for k in KEYWORDS[team]):
                posts.append(title)

    except Exception as e:
        print("RSS failed:", e)

    return posts

# ---------- RUN ----------
def run(team):
    posts = fetch_all(team)

    if len(posts) < 5:
        save_row(team, 50, len(posts))
        return

    scores = [score_text(p) for p in posts]
    avg = sum(scores) / len(scores)

    save_row(team, avg, len(posts))

if __name__ == "__main__":
    import sys
    run(sys.argv[1])
