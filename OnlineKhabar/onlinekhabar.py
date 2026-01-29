import requests
import csv
import time
import re
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
OUTPUT_FILE = "Onlinekhabar/Onlinekhabar.csv"

# ---------------- HELPERS ----------------

def clean_text(text):
    return " ".join(text.split())

def remove_dateline(text):
    # Remove leading dateline like "KATHMANDU, Jan 12:" from Republica / OnlineKhabar
    return re.sub(r'^[A-Z\s]+,\s+[A-Za-z]+\s+\d{1,2}:\s*', '', text)



# ---------------- ONLINEKHABAR ----------------

def extract_onlinekhabar(url):
    soup = BeautifulSoup(
        requests.get(url, headers=HEADERS, timeout=15).text, "lxml"
    )

    # Title
    title_tag = soup.select_one("div.ok-post-header h1")
    title = title_tag.text.strip() if title_tag else ""

    # Category
    cat = soup.select_one('a[href*="/category/"]')
    category = cat.text.strip() if cat else ""

    # Date
    date_meta = soup.find("meta", property="article:published_time")
    date = date_meta["content"][:10] if date_meta else ""

    # Body
    content = soup.find("div", class_="post-content-wrap")
    paragraphs = []
    if content:
        for p in content.find_all("p"):
            txt = clean_text(p.get_text())
            if len(txt) > 40:
                # remove dateline like "Kathmandu, January 28"
                txt = re.sub(r'^[A-Z][a-z]+,\s+[A-Za-z]+\s+\d{1,2}', '', txt)
                paragraphs.append(txt)

    return {
        "CATEGORY": category,
        "TITLE": title,
        "BODY": "\n\n".join(paragraphs),
        "SOURCE": "OnlineKhabar",
        "DATE": date,
    }


# ---------------- ROUTER ----------------

def extract_article(url):
    if "onlinekhabar.com" in url:
        return extract_onlinekhabar(url)
    return None

# ---------------- BATCH RUN ----------------

def run_batch():
    with open("onlinekhabar/okurls.txt") as f:
        urls = [u.strip() for u in f if u.strip()]

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(
            ["ID", "CATEGORY", "LINK", "TITLE", "BODY", "SOURCE", "DATE"]
        )

        for i, url in enumerate(urls, start=1):
            try:
                data = extract_article(url)
                if not data:
                    continue

                writer.writerow([
                    i,
                    data["CATEGORY"],
                    url,
                    data["TITLE"],
                    data["BODY"],
                    data["SOURCE"],
                    data["DATE"]
                ])

                print(f"[OK] {i}: {url}")
                time.sleep(2)

            except Exception as e:
                print(f"[FAIL] {url} → {e}")
                time.sleep(5)

if __name__ == "__main__":
    run_batch()