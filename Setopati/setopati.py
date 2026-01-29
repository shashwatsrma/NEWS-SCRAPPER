import requests
import csv
import time
import re
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
OUTPUT_FILE = "setopati/setopati.csv"

# ---------------- HELPERS ----------------

def clean_text(text):
    return " ".join(text.split())

def remove_dateline(text):
    # Remove leading dateline like "KATHMANDU, Jan 12:" from Republica / OnlineKhabar
    return re.sub(r'^[A-Z\s]+,\s+[A-Za-z]+\s+\d{1,2}:\s*', '', text)



# ---------------- SETOPATI ----------------

def extract_setopati(url):
    soup = BeautifulSoup(
        requests.get(url, headers=HEADERS, timeout=15).text, "lxml"
    )

    # Title
    title_tag = soup.select_one("div.title-names span.news-big-title")
    title = title_tag.text.strip() if title_tag else ""

    # Date from published-date span
    date_span = soup.select_one("div.published-date span.pub-date")
    if date_span:
        # Remove "Published Date: " prefix and take only YYYY-MM-DD
        date_text = date_span.text.strip().replace("Published Date:", "").strip()
        date = date_text[:10]  # "2026-01-27"
    else:
        date = ""

    # Category from URL
    category = url.split("/")[3].replace("-", " ").title()

    # Body
    editor = soup.find("div", class_="editor-box")
    paragraphs = []
    if editor:
        for p in editor.find_all("p"):
            txt = clean_text(p.get_text())
            if len(txt) > 40:
                paragraphs.append(txt)

    return {
        "CATEGORY": category,
        "TITLE": title,
        "BODY": "\n\n".join(paragraphs),
        "SOURCE": "Setopati",
        "DATE": date,
    }

# ---------------- ROUTER ----------------

def extract_article(url):
    
    if "setopati.com" in url:
        return extract_setopati(url)
    
    return None

# ---------------- BATCH RUN ----------------

def run_batch():
    with open("setopati/setopatiurls.txt") as f:
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