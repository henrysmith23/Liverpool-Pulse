# ABOUTME: Scrapes the latest posts from the Liverpool forum thread using Playwright.
# ABOUTME: Calculates sentiment scores and saves results for the Streamlit dashboard.

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
from sentiment import score_text
from db import save_row

THREAD_URL = "https://anfield.freeforums.net/thread/755/liverpool-season-richard-hughes-farce"

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
def get_page_html(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        page = context.new_page()

        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(10000)

        html = page.content()
        title = page.title()

        print(f"Page title: {title}")
        print(f"HTML length: {len(html)}")

        browser.close()

    return html


def get_last_page_number():
    html = get_page_html(THREAD_URL)
    soup = BeautifulSoup(html, "html.parser")

    # Try multiple pagination selectors common on ProBoards
    for selector in ["ul.ui-pagination", "div.pagination", "ul.pagination", "nav.pagination"]:
        pagination = soup.select_one(selector)
        if pagination:
            break

    if not pagination:
        # Fallback: look for any element with page numbers as links
        import re
        page_links = soup.find_all("a", href=re.compile(r"\?page=\d+"))
        if page_links:
            max_page = 1
            for link in page_links:
                match = re.search(r"\?page=(\d+)", link.get("href", ""))
                if match:
                    num = int(match.group(1))
                    if num > max_page:
                        max_page = num
            print(f"Found last page via href scan: {max_page}")
            return max_page

        print("WARNING: No pagination found, defaulting to page 1")
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

    print(f"Found last page: {max_page}")
    return max_page


def fetch_posts():
    last_page = get_last_page_number()
    url = f"{THREAD_URL}?page={last_page}"
    print(f"Fetching page {last_page}: {url}")

    html = get_page_html(url)
    soup = BeautifulSoup(html, "html.parser")

    posts = []

    # Strategy 1: ProBoards uses <tr> with class "post" or "item"
    post_rows = soup.select("tr.item.post")
    if not post_rows:
        post_rows = soup.select("tr.post")
    if not post_rows:
        post_rows = soup.select("div.post")
    if not post_rows:
        # Strategy 2: look for elements with data-post-id
        post_rows = soup.find_all(attrs={"data-post-id": True})

    print(f"Post containers found (strategy 1/2): {len(post_rows)}")

    if post_rows:
        for row in post_rows:
            try:
                post_id = row.get("data-post-id") or row.get("id", "").replace("post-", "")
                if not post_id:
                    import re as _re
                    link = row.find("a", href=_re.compile(r"/post/(\d+)"))
                    if link:
                        match = _re.search(r"/post/(\d+)", link["href"])
                        if match:
                            post_id = match.group(1)
                if not post_id:
                    continue

                # Find author
                author_tag = row.select_one(
                    "a.user-link, a.username, .author a, .post-author a, a[href*='/user/']"
                )
                author = author_tag.get_text(strip=True) if author_tag else "Unknown"

                # Find message content
                msg = row.select_one(
                    ".message, .post-body, .post-content, .content, .post_content"
                )
                if not msg:
                    msg = row.find(
                        "div",
                        class_=lambda c: c and ("content" in c.lower() or "message" in c.lower()),
                    )
                if not msg:
                    # Last resort: largest text block in the post container
                    divs = row.find_all("div")
                    longest = None
                    longest_len = 0
                    for d in divs:
                        t = d.get_text(strip=True)
                        if len(t) > longest_len:
                            longest = d
                            longest_len = len(t)
                    if longest and longest_len > 20:
                        msg = longest
                if not msg:
                    continue
                text = msg.get_text(strip=True)

                # Find timestamp
                ts_tag = row.select_one(
                    "abbr[data-timestamp], time[data-timestamp], span[data-timestamp]"
                )
                if not ts_tag:
                    ts_tag = row.find(attrs={"data-timestamp": True})

                timestamp = 0
                if ts_tag:
                    timestamp = int(ts_tag.get("data-timestamp", 0))

                if timestamp == 0:
                    # Parse text-based timestamp from .post-date or similar
                    date_el = row.select_one(".post-date, .date, .time, .timestamp")
                    if not date_el:
                        date_el = row.find(
                            lambda tag: tag.name in ("span", "time", "abbr")
                            and tag.get_text(strip=True)
                            and "202" in tag.get_text(strip=True)
                        )
                    if date_el:
                        from dateutil import parser as dateparser
                        try:
                            dt = dateparser.parse(date_el.get_text(strip=True))
                            if dt:
                                timestamp = int(dt.timestamp() * 1000)
                        except (ValueError, TypeError):
                            pass

                if post_id and text:
                    posts.append({
                        "id": str(post_id),
                        "timestamp": timestamp,
                        "text": text,
                        "author": author
                    })
            except Exception as e:
                print(f"Error parsing post: {e}")
                continue
    if post_rows and not posts:
        # Posts containers found but no content extracted — log debug info
        sample = post_rows[0]
        print(f"DEBUG: Found {len(post_rows)} containers but extracted 0 posts.")
        print(f"DEBUG: Sample container tag={sample.name}, id={sample.get('id')}, classes={sample.get('class')}")
        inner_classes = set()
        for tag in sample.find_all(True, class_=True)[:30]:
            for c in tag.get("class", []):
                inner_classes.add(c)
        print(f"DEBUG: Inner classes in first post: {sorted(inner_classes)}")

    if not post_rows:
        # No containers found at all
        print("DEBUG: No posts found with known selectors.")
        print(f"DEBUG: All tag names in body: {set(tag.name for tag in soup.find_all(True)[:200])}")
        all_classes = set()
        for tag in soup.find_all(True, class_=True)[:200]:
            for c in tag.get("class", []):
                all_classes.add(c)
        print(f"DEBUG: Classes found: {sorted(list(all_classes))[:50]}")
        body_text = soup.get_text(strip=True)[:1000]
        print(f"DEBUG: Visible text: {body_text}")

    return posts


# ---------------- RUN ----------------
def run():
    posts = fetch_posts()

    print("TOTAL POSTS FOUND:", len(posts))

    seen = set(load_json(SEEN_FILE, []))
    last_run = load_json(LAST_RUN_FILE, 0)

    if last_run < 10**12:
        last_run = last_run * 1000

    new_posts = [
        p for p in posts
        if p["id"] not in seen and (p["timestamp"] == 0 or int(p["timestamp"]) > int(last_run))
    ]

    print("NEW POSTS FOUND:", len(new_posts))

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

    save_json(LATEST_POST_FILE, {
        "author": latest.get("author", "Unknown"),
        "text": latest["text"],
        "score": score_text(latest["text"])
    })


if __name__ == "__main__":
    run()
